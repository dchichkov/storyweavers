"""Typed authoring annotations, attached before grammar expansion or sampling.

The portable grammar is unchanged. Metadata is inert for its surface weights;
physical referents and nominal descriptions remain different sorts of binding.
"""
from dataclasses import replace
import json

from ..grammar import Node
from ..portable.features import NP, VP, Sentence


def metadata(node):
    return json.loads(node.attributes) if node.attributes else {}


def tagged(node, **attributes):
    return replace(node, attributes=json.dumps({**metadata(node), **attributes}, sort_keys=True))


def nominal(np):
    """Read a typed NP's binding; never infer identity from a matching noun."""
    def describe(node):
        if node.label.startswith(('referent:', 'scoped_referent:')):
            return dict(type='entity', entity=node.label.split(':', 1)[1])
        if 'nominal' in metadata(node):
            return metadata(node)['nominal']
        if node.label == 'gf.UsePron':
            from ..grammar import expand
            return dict(type='pronoun', form=next(expand(node))[0][0].lower())
        if node.label == 'local.ConjNP':
            return dict(type='coordination', members=[describe(c) for c in node.children
                                                      if c.kind != 'text'])
        if node.kind == 'choice':
            options = []
            for child in node.children:
                value = describe(child)
                if value not in options:
                    options.append(value)
            return options[0] if len(options) == 1 else dict(type='alternatives', options=options)
        if node.kind != 'text' and len(node.children) == 1:
            return describe(node.children[0])
        return dict(type='unresolved')
    return {**describe(np.subject), 'number': np.agreement.number, 'person': np.agreement.person}


def predicate(vp):
    result = dict(metadata(vp.tail).get('vp', {}))
    # Expanded grammar can substitute the lexical verb while retaining slots.
    result.update(lemma=vp.verb.base, construction=vp.label)
    return result


def tag_np(np, description):
    return replace(np, **{case: tagged(getattr(np, case), nominal=description)
                          for case in ('subject', 'object', 'possessive')})


class SemanticRules:
    """Mixin on SpeechLanguage: annotate the existing seven plans compositionally."""
    def cn(self, word, *adjectives):
        noun = super().cn(word, *adjectives)
        info = dict(type='nominal', lemma=word, modifiers=list(adjectives), mass=noun.mass)
        return replace(noun, singular=tagged(noun.singular, nominal=info),
                       plural=tagged(noun.plural, nominal=info))

    def n(self, word, *adjectives, det='the', number='singular'):
        np = super().n(word, *adjectives, det=det, number=number)
        return tag_np(np, dict(type='nominal', lemma=word, modifiers=list(adjectives),
                               determiner=det, number=number))

    def possess(self, owner, noun, number='singular'):
        np = super().possess(owner, noun, number)
        info = dict(metadata(noun.singular).get('nominal', {'type': 'unresolved'}))
        return tag_np(np, {**info, 'owner': nominal(owner), 'number': number})

    def v(self, word, *complements):
        vp = super().v(word, *complements)
        slots = {}
        if len(complements) == 1:
            obj = complements[0]
            if isinstance(obj, NP):
                slots['object'] = nominal(obj)
            elif isinstance(obj, VP):
                slots['action'] = predicate(obj)
            elif isinstance(obj, Sentence):
                slots['reported_clause'] = True
        elif len(complements) == 2:
            first, second = complements
            slots['recipient' if isinstance(second, NP) else 'object'] = nominal(first)
            slots['object' if isinstance(second, NP) else 'action'] = (
                nominal(second) if isinstance(second, NP) else predicate(second))
        return replace(vp, tail=tagged(vp.tail, vp=dict(lemma=word, arguments=slots,
                                                      modality=('attempt' if word in {'try', 'struggle'} else 'intention')
                                                      if 'action' in slots and word in {'want', 'hope', 'promise', 'choose', 'decide', 'ask', 'need', 'remember', 'try', 'struggle'} else 'plain')))

    def pp(self, preposition, obj):
        adv = super().pp(preposition, obj)
        return replace(adv, node=tagged(adv.node, modifier=dict(preposition=preposition, object=nominal(obj))))

    def adv(self, action, *modifiers):
        vp = super().adv(action, *modifiers)
        info = predicate(action)
        info['modifiers'] = info.get('modifiers', []) + [
            dict(adverb=m) if isinstance(m, str) else metadata(m.node).get('modifier', {'type': 'unresolved'})
            for m in modifiers]
        return replace(vp, tail=tagged(vp.tail, vp=info))

    def be(self, complement):
        vp = super().be(complement)
        info = dict(lemma='be', modality='state', arguments={},
                    complement=complement if isinstance(complement, str) else metadata(complement.node).get('modifier'))
        return replace(vp, tail=tagged(vp.tail, vp=info))

    def can(self, action):
        vp = super().can(action)
        return replace(vp, tail=tagged(vp.tail, vp=dict(lemma='can', modality='ability',
                                                      arguments={'action': predicate(action)})))

    def s(self, subject, action, *, negative=False, tense=None):
        if isinstance(subject, str):
            subject = self.ref(subject, subject=True)
        result = super().s(subject, action, negative=negative, tense=tense)
        info = dict(subject=nominal(subject), predicate=predicate(action),
                    tense=tense or self.tense, polarity='negative' if negative else 'positive')
        return replace(result, node=tagged(result.node, clause=info))
