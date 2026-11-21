"""Incremental joint distribution over word/attribute bundles.

A visible word conditions, rather than samples away, its latent annotations.
Derivation weights retain cross-token correlations. Attribute-only evidence can
condition the same posterior; subsequent words and final event selection use it.
"""
from collections import defaultdict
from copy import deepcopy
import json
import math

from ..grammar import Forest


class AttributeForest(Forest):
    def __init__(self, derivations, evidence, annotations, *, end_annotations=None):
        super().__init__(derivations, evidence)
        if len(annotations) != len(derivations):
            raise ValueError('one annotation sequence per derivation required')
        if end_annotations is not None and len(end_annotations) != len(derivations):
            raise ValueError('one END annotation per derivation required')
        self.attribute_table = {}
        interned = {}
        self.attribute_ids = []
        for index, (derivation, sequence) in enumerate(zip(self.derivations, annotations)):
            if len(sequence) != len(derivation.tokens):
                raise ValueError('annotation length does not match terminal sequence')
            end = dict(pos='END', event=dict(name=derivation.frame.kind.replace('_', ' '),
                       source_kind=derivation.frame.kind, status='proposed', scope='candidate_scene',
                       roles={key: getattr(derivation.frame, key) for key in
                              ('actor', 'patient', 'instrument', 'destination') if getattr(derivation.frame, key)}))
            if end_annotations is not None:
                end = deepcopy(end_annotations[index])
            ids = []
            for attributes in (*sequence, end):
                canonical = json.dumps(attributes, sort_keys=True, separators=(',', ':'))
                if canonical not in interned:
                    aid = f'a{len(interned)}'
                    interned[canonical] = aid
                    self.attribute_table[aid] = deepcopy(attributes)
                ids.append(interned[canonical])
            self.attribute_ids.append(tuple(ids))
        self.weights = {i: d.probability for i, d in enumerate(self.derivations)}
        self.prefix = ()
        self.complete = False
        self.revision = 0

    def predict(self, prefix=()):
        if tuple(prefix) != self.prefix or self.complete:
            raise ValueError('predict must follow the live annotated prefix')
        total = sum(self.weights.values())
        mass, joint = defaultdict(float), defaultdict(float)
        explanations, rules = defaultdict(lambda: defaultdict(float)), defaultdict(set)
        position = len(prefix)
        for i, weight in self.weights.items():
            d = self.derivations[i]
            word = d.tokens[position] if position < len(d.tokens) else '<END>'
            mass[word] += weight
            joint[word, self.attribute_ids[i][position]] += weight
            explanations[word][d.frame.kind] += weight
            rules[word].update(d.rules)
        choices = [dict(word=word, probability=mass[word]/total,
                        events={k: v/mass[word] for k, v in sorted(explanations[word].items())},
                        grammar_rules=sorted(rules[word]))
                   for word in sorted(mass, key=lambda w: (-mass[w], w))]
        return dict(prefix=list(prefix), choices=choices, complete='<END>' in mass,
                    prefix_probability=sum(d.probability for d in super().survivors(prefix)),
                    surviving_derivations=len(self.weights), attribute_revision=self.revision,
                    annotated_choices=[dict(word=w, attributes=a, probability=p/total)
                                       for (w, a), p in joint.items()])

    @staticmethod
    def reconcile_word_weights(prediction):
        """Lift existing word-head scores into the joint, preserving P(attrs|word)."""
        totals = defaultdict(float)
        for row in prediction['annotated_choices']:
            totals[row['word']] += row['probability']
        desired = {c['word']: c['probability'] for c in prediction['choices']}
        if set(desired) != set(totals):
            raise ValueError('word reranker changed grammar support')
        for row in prediction['annotated_choices']:
            row['probability'] *= desired[row['word']] / totals[row['word']]
        return prediction

    def rerank_attributes(self, prediction, factors):
        """Apply authored attribute/head multipliers to the joint, then remarginalize.

        Factors key complete bundles, not independent attribute marginals. This
        also permits two identical visible words to receive different weights.
        """
        if prediction['attribute_revision'] != self.revision or tuple(prediction['prefix']) != self.prefix:
            raise ValueError('stale annotated prediction')
        active = {r['attributes'] for r in prediction['annotated_choices']}
        if not set(factors) <= active or any(not math.isfinite(v) or v <= 0 for v in factors.values()):
            raise ValueError('positive finite factors for active attribute bundles required')
        rows = prediction['annotated_choices']
        total = sum(r['probability'] * factors.get(r['attributes'], 1.) for r in rows)
        if not math.isfinite(total) or total <= 0:
            raise ValueError('invalid attribute normalization')
        masses, events = defaultdict(float), defaultdict(lambda: defaultdict(float))
        # A bundle is shared only within one complete set of correlated fields.
        # Resolve event kind from the underlying rows even for minimal test bundles.
        position = len(self.prefix)
        kinds = {}
        for i in self.weights:
            d = self.derivations[i]
            word = d.tokens[position] if position < len(d.tokens) else '<END>'
            kinds.setdefault((word, self.attribute_ids[i][position]), defaultdict(float))[d.frame.kind] += self.weights[i]
        for r in rows:
            r['probability'] *= factors.get(r['attributes'], 1.) / total
            masses[r['word']] += r['probability']
            group = kinds[r['word'], r['attributes']]
            denominator = sum(group.values())
            for kind, weight in group.items():
                events[r['word']][kind] += r['probability'] * weight/denominator
        for c in prediction['choices']:
            c['probability'] = masses[c['word']]
            c['events'] = {kind: mass/c['probability'] for kind, mass in sorted(events[c['word']].items())}
        return prediction

    def observe(self, word, prediction, *, attribute_id=None):
        """Condition the correlated lattice on the observed surface (and optional binding)."""
        if self.complete or prediction['attribute_revision'] != self.revision or tuple(prediction['prefix']) != self.prefix:
            raise ValueError('stale annotated prediction')
        position = len(self.prefix)
        offered = {(r['word'], r['attributes']): r['probability'] for r in prediction['annotated_choices']}
        if any(not math.isfinite(p) or p < 0 for p in offered.values()) or not math.isclose(sum(offered.values()), 1., abs_tol=1e-9):
            raise ValueError('invalid joint distribution')
        word_mass = defaultdict(float)
        for (candidate_word, _), probability in offered.items():
            word_mass[candidate_word] += probability
        if set(word_mass) != {c['word'] for c in prediction['choices']} or any(
                not math.isclose(c['probability'], word_mass[c['word']], abs_tol=1e-9) for c in prediction['choices']):
            raise ValueError('word probabilities do not match joint marginals')
        group_mass = defaultdict(float)
        for i, weight in self.weights.items():
            d = self.derivations[i]
            w = d.tokens[position] if position < len(d.tokens) else '<END>'
            group_mass[w, self.attribute_ids[i][position]] += weight
        if set(offered) != set(group_mass):
            raise ValueError('joint reranker changed candidate support')
        updated = {}
        for i, weight in self.weights.items():
            d = self.derivations[i]
            w = d.tokens[position] if position < len(d.tokens) else '<END>'
            aid = self.attribute_ids[i][position]
            if w == word and (attribute_id is None or aid == attribute_id):
                updated[i] = weight * offered[w, aid] / group_mass[w, aid]
        total = sum(updated.values())
        if total <= 0:
            raise ValueError('observation has no compatible annotated candidate')
        self.weights = {i: weight/total for i, weight in updated.items() if weight > 0}
        self.revision += 1
        self.complete = word == '<END>'
        if not self.complete:
            self.prefix += (word,)
        posterior = defaultdict(float)
        for i, weight in self.weights.items():
            posterior[self.attribute_ids[i][position]] += weight
        return [dict(attributes=a, probability=p) for a, p in posterior.items()]

    def attribute_memory(self):
        """Last emitted token's CURRENT posterior; no future chosen annotation."""
        if not self.prefix:
            return []
        position = len(self.prefix)-1
        mass = defaultdict(float)
        for i, weight in self.weights.items():
            mass[self.attribute_ids[i][position]] += weight
        return [dict(attributes=self.attribute_table[aid], probability=p) for aid, p in mass.items()]

    def event_posterior(self, tokens):
        if tuple(tokens) != self.prefix or not self.complete:
            raise ValueError('condition on END before committing an event')
        mass = defaultdict(float)
        for i, weight in self.weights.items():
            mass[self.derivations[i].frame] += weight
        return dict(mass)
