"""Small, data-only conjunctive grammar induction for token/POS latents.

The hypothesis language is suffix-relative equality tests and conjunctions.
Bottom-up proposals come only from co-occurring input facts; no English rules,
target features in the input, or predeclared POS classes are supplied. Selected
predicates compile into one residual-writing layer and a joint grammar readout.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations
import math

from .grammar import Gap, GrammarNeuron, Rule, Seq, Token, canonical, positive
from .transformer import GrammarHead, GrammarProjection, Storyformer, StoryformerBlock


def token_pos(record):
    if (not isinstance(record, dict) or set(record) != {"token", "pos"} or
            any(not isinstance(record[key], str) or not record[key] for key in ("token", "pos"))):
        raise ValueError("this baseline requires exactly nonempty token and pos strings")
    return {"token": record["token"], "pos": record["pos"]}


def examples(documents, context_size=16):
    """Each target is excluded from its context, including its POS annotation."""
    for document in documents:
        rows = [token_pos(row) for row in document]
        for index, target in enumerate(rows):
            yield rows[max(0, index - context_size):index], target


@dataclass(frozen=True, order=True)
class Atom:
    offset: int
    field: str
    value: str


@dataclass(frozen=True, order=True)
class Clause:
    atoms: tuple = ()

    def matches(self, context):
        if not self.atoms:
            return not context
        return all(len(context) >= -atom.offset and context[atom.offset].get(atom.field) == atom.value
                   for atom in self.atoms)

    def pattern(self, context_size):
        if not self.atoms:
            return Seq()  # A learned empty-context production, not an input slot.
        width = -min(atom.offset for atom in self.atoms)
        tests = defaultdict(dict)
        for atom in self.atoms:
            tests[atom.offset][atom.field] = atom.value
        return Seq(Gap(maximum=context_size), *(Token(**tests[offset]) for offset in range(-width, 0)))

    def describe(self):
        return "<empty context>" if not self.atoms else " AND ".join(
            f"[{atom.offset}].{atom.field}={atom.value!r}" for atom in self.atoms)


@dataclass
class Proposal:
    clause: Clause
    rows: tuple
    support: int
    distribution: tuple
    cost: float


@dataclass
class InductionResult:
    model: Storyformer
    unigram: Storyformer
    rules: list
    history: list
    proposals: int
    vocabulary: list
    training_examples: int
    validation_history: list


def _compile(labels, clauses, weights, context_size, num_heads):
    heads, conditions = [], [Gap(maximum=context_size)]
    for index, clause in enumerate(clauses):
        if not clause.atoms:
            conditions.append(Seq())
            continue
        feature = f"__grammar_{index}"
        neuron = GrammarNeuron(f"learned_{index}", (
            Rule(clause.pattern(context_size), {feature: True}),))
        heads.append(GrammarHead(neuron))
        conditions.append(Seq(Gap(maximum=context_size), Token(**{feature: True})))
    roots = defaultdict(list)
    for condition, row in zip(conditions, weights):
        for (word, pos), weight in zip(labels, row):
            roots[word].append(Rule(condition, {"pos": pos}, weight))
    projection = GrammarProjection({word: GrammarNeuron(word, tuple(rules)) for word, rules in roots.items()})
    features = {f"__grammar_{index}": dict(type="boolean", description=clause.describe(), origin="learned")
                for index, clause in enumerate(clauses) if clause.atoms}
    return Storyformer(projection, layers=(StoryformerBlock(tuple(heads), num_heads),),
                       context_size=context_size, top_k=10, features=features)


def _matrices(rows, proposals, prior, amplitudes):
    masses = [list(prior) for _ in rows]
    totals = [1.] * len(rows)
    for proposal, amplitude in zip(proposals, amplitudes):
        for index in proposal.rows:
            totals[index] += amplitude
            for label, probability in enumerate(proposal.distribution):
                masses[index][label] += amplitude * probability
    return masses, totals


def _log_likelihood(rows, masses, totals):
    return math.fsum(count * (math.log(masses[index][label]) - math.log(totals[index]))
                     for index, (_, counts) in enumerate(rows) for label, count in counts.items())


def _gain(proposal, rows, masses, totals, amplitude):
    return math.fsum(
        math.fsum(count * math.log1p(amplitude * proposal.distribution[label] / masses[index][label])
                  for label, count in rows[index][1].items())
        - sum(rows[index][1].values()) * math.log1p(amplitude / totals[index])
        for index in proposal.rows)


def _fit_weights(rows, proposals, weights, steps, learning_rate):
    """Exact batch log-weight gradients, aggregated by identical causal prefixes."""
    active = [[0] for _ in rows]
    for rule, proposal in enumerate(proposals, 1):
        for index in proposal.rows:
            active[index].append(rule)
    size = sum(sum(counts.values()) for _, counts in rows)
    for _ in range(steps):
        gradients = [[0.] * len(weights[0]) for _ in weights]
        for (_, counts), rules in zip(rows, active):
            mass = [math.fsum(weights[rule][label] for rule in rules) for label in range(len(weights[0]))]
            total, observations = math.fsum(mass), sum(counts.values())
            for rule in rules:
                for label, weight in enumerate(weights[rule]):
                    gradients[rule][label] += weight * (counts.get(label, 0) / mass[label] - observations / total)
        for rule, row in enumerate(weights):
            for label, weight in enumerate(row):
                row[label] = math.exp(max(-40., min(40., math.log(weight) + learning_rate * gradients[rule][label] / size)))
    return weights


def induce(documents, *, validation_documents=None, context_size=16, lookback=3, max_literals=2, max_rules=16,
           num_heads=16, min_support=8, smoothing=1., complexity=.5,
           weight_steps=80, learning_rate=4., max_proposals=10000):
    """Learn conjunction structure and output weights; return a normal Storyformer.

    Greedy selection maximizes conditional log-likelihood improvement minus a
    description-length cost. Other observed continuations compete probabilistically;
    they are not forbidden outputs. Search is finite, with an explicit proposal cap.
    Optional validation examples veto rules that fail to improve held-out likelihood;
    they never supply candidate literals, lexical entries, or fitted weights.
    """
    integers = (context_size, lookback, max_literals, num_heads, min_support, max_proposals)
    if any(type(value) is not int or value < 1 for value in integers):
        raise ValueError("context, search bounds, head slots and support must be positive integers")
    if type(max_rules) is not int or not 0 <= max_rules <= num_heads:
        raise ValueError("max_rules must fit the layer's head slots")
    if type(weight_steps) is not int or weight_steps < 0 or lookback > context_size:
        raise ValueError("invalid weight steps or lookback")
    positive(smoothing, "smoothing")
    positive(complexity, "complexity", zero=True)
    positive(learning_rate, "learning rate")
    grouped, contexts, inventory = defaultdict(Counter), {}, Counter()
    for context, target in examples(documents, context_size):
        key, label = canonical(context), (target["token"], target["pos"])
        grouped[key][label] += 1
        contexts[key] = context
        inventory[label] += 1
    if not inventory:
        raise ValueError("at least one token/POS training target is required")
    labels = sorted(inventory)
    label_ids = {label: index for index, label in enumerate(labels)}
    rows = [(contexts[key], Counter({label_ids[label]: n for label, n in grouped[key].items()}))
            for key in sorted(grouped)]
    validation_rows = []
    if validation_documents is not None:
        validation_groups, validation_contexts = defaultdict(Counter), {}
        for context, target in examples(validation_documents, context_size):
            label = target["token"], target["pos"]
            if label not in label_ids:
                raise ValueError(f"validation target outside training vocabulary: {label}")
            key = canonical(context)
            validation_groups[key][label_ids[label]] += 1
            validation_contexts[key] = context
        validation_rows = [(validation_contexts[key], validation_groups[key]) for key in sorted(validation_groups)]
        if not validation_rows:
            raise ValueError("validation documents must contain at least one target")
    size = sum(inventory.values())
    prior = tuple((inventory[label] + smoothing / len(labels)) / (size + smoothing) for label in labels)
    domains = {field: len({label[index] for label in labels}) for index, field in enumerate(("token", "pos"))}

    covered = defaultdict(list)
    for index, (context, _) in enumerate(rows):
        if not context:
            covered[Clause()].append(index)
            continue
        atoms = sorted(Atom(offset, field, context[offset][field])
                       for offset in range(-min(len(context), lookback), 0) for field in ("token", "pos"))
        for length in range(1, min(max_literals, len(atoms)) + 1):
            for conjunction in combinations(atoms, length):
                clause = Clause(conjunction)
                covered[clause].append(index)
                if len(covered) > max_proposals:
                    raise ValueError("proposal budget exceeded; reduce lookback or max_literals")
    proposals, signatures = [], set()
    # Prefer the shorter/cheaper condition when training coverage is identical.
    def description(clause):
        return 1. + sum(1. + math.log2(lookback * domains[atom.field] * -atom.offset)
                        for atom in clause.atoms)
    for clause in sorted(covered, key=lambda clause: (description(clause), clause)):
        indices = tuple(covered[clause])
        counts = Counter()
        for index in indices:
            counts.update(rows[index][1])
        support = sum(counts.values())
        if support < min_support or indices in signatures:
            continue
        signatures.add(indices)
        distribution = tuple((counts[label] + smoothing * prior[label]) / (support + smoothing)
                             for label in range(len(labels)))
        proposals.append(Proposal(clause, indices, support, distribution, description(clause)))

    selected, amplitudes, learned = [], [], []
    masses, totals = _matrices(rows, selected, prior, amplitudes)
    history = [-_log_likelihood(rows, masses, totals) / size]
    validation_proposals = {proposal.clause: Proposal(
        proposal.clause, tuple(index for index, (context, _) in enumerate(validation_rows)
                               if proposal.clause.matches(context)),
        0, proposal.distribution, proposal.cost) for proposal in proposals}
    validation_masses, validation_totals = _matrices(validation_rows, [], prior, [])
    validation_size = sum(sum(counts.values()) for _, counts in validation_rows)
    validation_history = ([-_log_likelihood(validation_rows, validation_masses, validation_totals) / validation_size]
                          if validation_size else [])
    remaining = list(proposals)
    for _ in range(max_rules):
        best = None
        for proposal in remaining:
            for amplitude in (.5, 2., 8., 32.):
                gain = _gain(proposal, rows, masses, totals, amplitude)
                utility = gain - complexity * proposal.cost
                if utility > 0 and (best is None or utility > best[0]):
                    validation_gain = (_gain(validation_proposals[proposal.clause], validation_rows,
                                             validation_masses, validation_totals, amplitude)
                                       if validation_size else None)
                    if validation_gain is None or validation_gain > 0:
                        best = utility, proposal, amplitude, gain, validation_gain
        if best is None:
            break
        utility, proposal, amplitude, gain, validation_gain = best
        selected.append(proposal)
        amplitudes.append(amplitude)
        remaining.remove(proposal)
        learned.append(dict(condition=proposal.clause.describe(), support=proposal.support,
                            gain_nats=gain, penalized_gain=utility, initial_strength=amplitude,
                            validation_gain_nats=validation_gain,
                            atoms=[vars(atom) for atom in proposal.clause.atoms]))
        masses, totals = _matrices(rows, selected, prior, amplitudes)
        history.append(-_log_likelihood(rows, masses, totals) / size)
        if validation_size:
            validation_masses, validation_totals = _matrices(
                validation_rows, [validation_proposals[proposal.clause] for proposal in selected], prior, amplitudes)
            validation_history.append(-_log_likelihood(validation_rows, validation_masses, validation_totals) / validation_size)
    weights = [list(prior), *[[amplitude * p for p in proposal.distribution]
                              for proposal, amplitude in zip(selected, amplitudes)]]
    _fit_weights(rows, selected, weights, weight_steps, learning_rate)
    head_slot = 0
    for index, (proposal, row, report) in enumerate(zip(selected, weights[1:], learned)):
        total = math.fsum(row)
        report["output_strength"] = total
        report["outputs"] = [dict(token=labels[label][0], pos=labels[label][1], probability=row[label] / total)
                             for label in sorted(range(len(labels)), key=lambda label: (-row[label], labels[label]))[:10]]
        report["next_pos"] = {pos: math.fsum(weight for (_, value), weight in zip(labels, row) if value == pos) / total
                              for pos in sorted({pos for _, pos in labels})}
        report["head_slot"] = head_slot if proposal.clause.atoms else None
        report["residual_feature"] = f"__grammar_{index}" if proposal.clause.atoms else None
        head_slot += bool(proposal.clause.atoms)
    model = _compile(labels, [proposal.clause for proposal in selected], weights, context_size, num_heads)
    unigram = _compile(labels, [], [prior], context_size, num_heads)
    return InductionResult(model, unigram, learned, history, len(proposals),
                           [dict(token=word, pos=pos) for word, pos in labels], size, validation_history)
