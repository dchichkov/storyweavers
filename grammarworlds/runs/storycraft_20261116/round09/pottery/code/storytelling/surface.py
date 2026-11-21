"""Typed speech/scene constructions layered over the frozen portable grammar."""
from copy import deepcopy
from dataclasses import dataclass, field

from ..grammar import Node, seq
from ..portable.language import Language
from ..portable.nouns import pronoun
from .scene_families import SceneFamilies
from .semantic_rules import SemanticRules

from .lexicon import SHARED as EXTRA



class SpeechLanguage(SceneFamilies, SemanticRules, Language):
    def __init__(self, world, tense="past", lexicon=None):
        super().__init__(world, tense)
        self.lexicon = deepcopy(self.lexicon)
        for additions in (EXTRA, lexicon or {}):
            for category, entries in additions.items():
                self.lexicon[category].update(deepcopy(entries))

    def ref(self, entity_id, *, subject=False, first=False, adjectives=()):
        # A pronoun may continue the last visible actor only when its physical
        # antecedent is unique. Hidden operations never establish a referent.
        visible = next((e for e in reversed(self.world.history) if e.get("narrated")), None)
        continue_actor = bool(visible and visible["frame"]["actor"] == entity_id
            and entity_id in visible.get("referents", ())
            and set(visible.get("speakers", ())) <= {entity_id})
        known = entity_id in self.discourse.resolve()
        e = self.world.entities[entity_id]
        self.discourse.introduce(entity_id, pronoun=e.pronoun, number=e.number)
        return super().ref(entity_id, subject=subject and known and continue_actor,
                           first=first, adjectives=adjectives)

    @staticmethod
    def tag_subject(subject, sentence):
        """Preserve explicit entity/coordination bindings; never guess possessors."""
        from ..portable.features import Sentence
        def entities(node):
            if node.label.startswith('referent:'):
                return [node.label.split(':', 1)[1]]
            if node.label == 'local.ConjNP':
                return [e for child in node.children if isinstance(child, Node) for e in entities(child)]
            return []
        result = sentence.node
        for entity in sorted(set(entities(subject.subject))):
            result = seq('clause.subject:'+entity, result)
        return Sentence(result)

    def s(self, subject, predicate, *, negative=False, tense=None):
        if isinstance(subject, str):
            subject = self.ref(subject, subject=True)
        return self.tag_subject(subject, super().s(subject, predicate, negative=negative, tense=tense))

    def line(self, speaker, content, *, listener=None):
        if speaker not in self.world.entities or self.world.entities[speaker].kind != "person":
            raise ValueError("dialogue needs a physical speaker")
        if listener is not None and self.world.entities[speaker].location != self.world.entities[listener].location:
            raise ValueError("dialogue participants must be together")
        # Quotes are explicit grammar terminals, not lost to legacy text tokenization.
        result = seq("dialogue.speaker:" + speaker, self.ref(speaker).subject,
                   "said" if self.tense == "past" else "says", ",",
                   Node("text", "quote.open", ("“",)), content.node, ".",
                   Node("text", "quote.close", ("”",)))
        return seq(f"dialogue.listener:{speaker}:{listener}", result) if listener is not None else result

    def me(self, vp, *, negative=False):
        return self.s(pronoun("I"), vp, tense="present", negative=negative)

    def you(self, vp, *, negative=False):
        return self.s(pronoun("you"), vp, tense="present", negative=negative)

    def using(self, actor, action, instrument):
        """Two constructions for the same grounded instrument/action relation."""
        return self.either(self.s(actor, self.v("use", instrument, action)),
                           self.s(actor, self.adv(action, self.pp("with", instrument))))

    def counted(self, count, noun, *modifiers):
        """A bounded cardinal NP with agreement, used for physical quantities."""
        from ..portable import nouns
        from ..portable.features import NP
        if type(count) is not int or not 1 <= count <= 4:
            raise ValueError("supported counts are one through four")
        common = self.cn(noun)
        for modifier in modifiers:
            common = nouns.adv_cn(common, modifier)
        base = nouns.det_cn(common, "bare", "singular" if count == 1 else "plural")
        word = ("one", "two", "three", "four")[count-1]
        return NP(*(seq("story.cardinal", word, getattr(base, case))
                    for case in ("subject", "object", "possessive")), base.agreement)


@dataclass
class Scene:
    node: Node
    claims: list[dict] = field(default_factory=list)


def scene(*parts, qa=()):
    """Claims annotate the selected scene; only visible realized scenes feed QA."""
    from ..portable.features import Sentence
    nodes = [Language.utter(p) if isinstance(p, Sentence) else p for p in parts]
    return Scene(seq("story.scene", *nodes), list(qa))


def claim(key, kind, question, answer, *entities, supports=(), evidence_only=False):
    """Optional semantic claim keys name additional narrated evidence required."""
    return dict(key=key, kind=kind, question=question, answer=answer,
                entities=list(entities), supports=list(supports),
                **({'evidence_only':True} if evidence_only else {}))


def detokenize(tokens):
    """Punctuation formatting only; words/quotes all come from the sampled forest."""
    out, capitalize = "", True
    for token in tokens:
        if token in {",", ";", ".", "!", "?", "”"}:
            out += token
            if token in {".", "!", "?"}:
                capitalize = True
        elif token == "“":
            out += (" " if out else "") + token
            capitalize = True
        else:
            if capitalize:
                token = token[:1].upper() + token[1:]
            out += ("" if not out or out.endswith("“") else " ") + token
            capitalize = False
    return out
