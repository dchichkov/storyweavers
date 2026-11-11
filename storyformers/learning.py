"""Small fixed-structure batch learner and evidence collector; no API calls.

Execute every causal training position once, then reuse its grammar derivations
for exact output log-weight gradients. Rebuild the batch after any structural
edit. Heads remain discrete programs; their weights are not differentiated.
"""

from collections import Counter, defaultdict
import json
import math

from .grammar import canonical, positive
from .neuron_review import model_fingerprint
from .transformer import JointDistribution, semantic


class LearningBatch:
    def __init__(self, model, documents):
        self.model = model
        self.base_model_sha256 = model_fingerprint(model)
        self.rules, self.rows, self.head_activations = [], [], Counter()
        rule_ids, grouped, contexts = {}, defaultdict(Counter), {}
        head_rules = {id(rule) for layer in model.layers for head in layer.heads if head
                      for rule in head.neuron.rules}
        for neuron in model.projection.neurons.values():
            for rule in neuron.rules:
                if id(rule) in head_rules:
                    raise ValueError("head and output weights must be separate")
                if id(rule) not in rule_ids:
                    rule_ids[id(rule)] = len(self.rules)
                    self.rules.append(rule)
        for context, target in model.examples(documents):
            key = canonical(context)
            contexts[key] = context
            grouped[key][canonical(semantic(target))] += 1
        if not grouped:
            raise ValueError("a learning batch needs targets")
        for key, counts in grouped.items():
            context = contexts[key]
            history, stream, trace = model._run(context)
            views = [row.view() for row in stream]
            activations = model.projection.activations(views)
            terms = [(rule_ids[id(neuron.rules[match.rule])],
                      match.mass / neuron.rules[match.rule].weight, latent)
                     for _, neuron, match, latent in activations]
            targets = []
            for encoded, count in counts.items():
                target = json.loads(encoded)
                good = [i for i, (_, _, latent) in enumerate(terms) if self.matches(latent, target)]
                targets.append((target, count, good))
            observations = sum(counts.values())
            for event in trace:
                if history and event["query"] == history[-1]["position"]["token"]:
                    self.head_activations[f"L{event['layer']}.H{event['head']}:{event['neuron']}"] += observations
            self.rows.append((context, views, terms, targets))
        self.targets = sum(count for _, _, _, targets in self.rows for _, count, _ in targets)

    @staticmethod
    def matches(latent, target):
        return all(canonical(latent.get(key)) == canonical(value) for key, value in target.items())

    def _assert_current(self):
        if model_fingerprint(self.model) != self.base_model_sha256:
            raise ValueError("stale learning batch: rebuild after external weight or structure edits")

    def fit(self, *, steps=80, learning_rate=4.):
        """Full-batch likelihood gradients, including all outputs before top-k."""
        self._assert_current()
        positive(learning_rate, "learning rate")
        if type(steps) is not int or steps < 0:
            raise ValueError("steps must be nonnegative")
        if any(not good for _, _, _, targets in self.rows for _, _, good in targets):
            raise ValueError("target outside output grammar support; propose structure first")
        history = []
        for _ in range(steps):
            gradients, loss = [0.] * len(self.rules), 0.
            for _, _, terms, targets in self.rows:
                masses = [self.rules[index].weight * factor for index, factor, _ in terms]
                total = math.fsum(masses)
                count_all = sum(count for _, count, _ in targets)
                for (index, _, _), mass in zip(terms, masses):
                    gradients[index] -= count_all * mass / total
                for _, count, good in targets:
                    correct = math.fsum(masses[i] for i in good)
                    loss -= count * math.log(correct / total)
                    for i in good:
                        gradients[terms[i][0]] += count * masses[i] / correct
            history.append(loss / self.targets)
            for rule, gradient in zip(self.rules, gradients):
                rule.weight = math.exp(max(-60., min(60., math.log(rule.weight)
                                                    + learning_rate * gradient / self.targets)))
        self.base_model_sha256 = model_fingerprint(self.model)
        return dict(steps=steps, learning_rate=learning_rate, training_nll_before_steps=history)

    def report(self, *, max_examples=12):
        self._assert_current()
        loss, supported, correct = 0., 0, 0
        pos_stats, examples = defaultdict(lambda: [0, 0, 0.]), []
        for context, views, terms, targets in self.rows:
            distribution = JointDistribution([(latent, self.rules[index].weight * factor)
                                              for index, factor, latent in terms], self.model.top_k)
            best = max(distribution.joint, key=lambda row: row["probability"], default=None)
            for target, count, _ in targets:
                p = distribution.probability(target)
                supported += count * (p > 0)
                correct += count * bool(best and self.matches(best["latent"], target))
                nll = -math.log(p) if p else None
                stats = pos_stats[target.get("pos")]
                stats[0] += count
                stats[1] += count * (p > 0)
                if nll is not None:
                    loss += count * nll
                    stats[2] += count * nll
                examples.append(dict(context=context, neuron_input=views, target=target, count=count,
                                     probability=p, top_tokens=distribution.probabilities))
        return dict(model_sha256=self.base_model_sha256, targets=self.targets, unique_prefixes=len(self.rows),
                    coverage=supported / self.targets, joint_nll=loss / self.targets if supported == self.targets else None,
                    joint_accuracy=correct / self.targets, head_activations=dict(self.head_activations),
                    per_pos={pos: dict(targets=n, coverage=ok / n, joint_nll=value / n if ok == n else None)
                             for pos, (n, ok, value) in pos_stats.items()},
                    high_loss_examples=sorted(examples, key=lambda row: row["probability"])[:max_examples])
