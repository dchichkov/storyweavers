#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pardon_moral_value_twist_folk_tale.py
======================================================================

A small folk-tale storyworld about a borrowed good, a hurt feeling, a pardon,
and a moral twist: a child or small villager does wrong, the harmed neighbor
shows mercy, and the ending reveals that the forgiven kindness returns in an
unexpected way.

The world is intentionally tiny and classical:
- a character owns something simple and valuable,
- another character takes or damages it,
- a serious feeling grows,
- the harmed character chooses pardon,
- a twist turns the loss into a gift or rescue.

The prose is state-driven rather than fixed-text swapping.  The same simulation
supports narration, QA, and an inline ASP twin for the simple combinatorial gate.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"damage": 0.0, "value": 0.0}
        if not self.memes:
            self.memes = {"hurt": 0.0, "guilt": 0.0, "mercy": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "daughter"}
        male = {"boy", "father", "man", "king", "son"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class StoryParams:
    villager: str
    villager_type: str
    wrongdoer: str
    wrongdoer_type: str
    harmed_good: str
    harmed_label: str
    harmed_kind: str
    helper: str
    helper_type: str
    twist: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Good:
    id: str
    label: str
    phrase: str
    kind: str
    value: float
    fragile: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Twist:
    id: str
    kind: str
    clue: str
    reveal: str
    gift: str
    value_bonus: float = 1.0
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_value(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters.get("damage", 0.0) >= THRESHOLD and ("value", e.id) not in world.fired:
            world.fired.add(("value", e.id))
            e.meters["value"] = max(0.0, e.meters.get("value", 0.0) - 1.0)
            out.append("__value__")
    return out


def _r_hurt(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters.get("damage", 0.0) >= THRESHOLD and ("hurt", e.id) not in world.fired:
            world.fired.add(("hurt", e.id))
            e.memes["hurt"] += 1
            out.append("__hurt__")
    return out


CAUSAL_RULES = [_r_value, _r_hurt]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(x for x in sents if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for helper in HELPERS:
        for twist in TWISTS:
            if helper.kind in {"priest", "miller", "widow"} and twist.kind in {"hidden_loaf", "lost_ring", "stolen_bell"}:
                combos.append((helper.id, twist.id, "yes"))
    return combos


def is_reasonable(helper: Twist, harmed: Good) -> bool:
    return helper.value_bonus >= 1.0 and harmed.fragile


def outcome_of(params: StoryParams) -> str:
    return "pardoned"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld about pardon, moral value, and a twist.")
    ap.add_argument("--villager", choices=VILLAGERS)
    ap.add_argument("--wrongdoer", choices=WRONGDOERS)
    ap.add_argument("--good", choices=GOODS)
    ap.add_argument("--twist", choices=TWISTS_BY_ID)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    villager = args.villager or rng.choice(list(VILLAGERS))
    wrongdoer = args.wrongdoer or rng.choice(list(WRONGDOERS))
    good_id = args.good or rng.choice(list(GOODS))
    twist_id = args.twist or rng.choice(list(TWISTS_BY_ID))
    return StoryParams(
        villager=villager,
        villager_type=VILLAGERS[villager],
        wrongdoer=wrongdoer,
        wrongdoer_type=WRONGDOERS[wrongdoer],
        harmed_good=good_id,
        harmed_label=GOODS[good_id].label,
        harmed_kind=GOODS[good_id].kind,
        helper=HELPERS_BY_KIND[TWISTS_BY_ID[twist_id].kind],
        helper_type=HELPERS[HELPERS_BY_KIND[TWISTS_BY_ID[twist_id].kind]].type,
        twist=twist_id,
    )


def _setup_world(params: StoryParams) -> World:
    w = World()
    villager = w.add(Entity(id=params.villager, kind="character", type=params.villager_type, role="harmed"))
    wrongdoer = w.add(Entity(id=params.wrongdoer, kind="character", type=params.wrongdoer_type, role="wrongdoer"))
    helper = w.add(Entity(id=params.helper, kind="character", type=params.helper_type, role="helper"))
    good = w.add(Entity(id="good", kind="thing", type=params.harmed_kind, label=params.harmed_label))
    good.meters["value"] = GOODS[params.harmed_good].value
    good.tags.update(GOODS[params.harmed_good].tags)
    w.facts.update(villager=villager, wrongdoer=wrongdoer, helper=helper, good=good, params=params)
    return w


def tell(world: World, params: StoryParams) -> None:
    v = world.get(params.villager)
    x = world.get(params.wrongdoer)
    h = world.get(params.helper)
    good = world.get("good")
    twist = TWISTS_BY_ID[params.twist]

    v.memes["mercy"] += 1
    x.memes["guilt"] += 1

    world.say(
        f"Long ago, in a small village, {v.id} kept {good.label_word} with care. "
        f"It was a humble thing, but it mattered in the little house."
    )
    world.say(
        f"One market morning, {x.id} took the {good.label_word} without asking. "
        f"By a stone fence, it slipped from {x.pronoun('possessive')} hands and broke."
    )
    good.meters["damage"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"{v.id} saw the broken {good.label_word} and felt the sting of it. "
        f'"Pardon," {x.id} whispered, head low as a bent reed.'
    )
    world.say(
        f"{v.id} was silent for a moment, then chose mercy instead of anger."
    )
    v.memes["mercy"] += 2
    x.memes["guilt"] += 1
    x.memes["joy"] += 1

    world.para()
    world.say(
        f"That was when the twist came: {twist.clue}. "
        f"{twist.reveal} So {v.id} did not lose the day after all."
    )
    good.meters["value"] += twist.value_bonus
    world.say(
        f"{v.id} let {x.id} keep the lesson and share the work, and {h.id} "
        f"helped make things right."
    )
    world.say(
        f"In the end, {twist.gift}, and the little village remembered that "
        f"forgiveness can turn a sorrow into a better thing."
    )

    world.facts["outcome"] = "pardoned"
    world.facts["twist"] = twist
    world.facts["lesson"] = "forgiveness turns sorrow toward repair"


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a folk tale for a child that includes the word "pardon" and ends with mercy.',
        f"Tell a small village story where {p.wrongdoer} breaks {p.villager}'s {p.harmed_label} and asks for pardon.",
        f"Write a moral tale with a twist: someone does wrong, is forgiven, and the ending proves kindness mattered.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    good = world.facts["good"]
    twist = world.facts["twist"]
    return [
        QAItem(
            question=f"What did {p.wrongdoer} ask for after breaking the {p.harmed_label}?",
            answer=f"{p.wrongdoer} asked for pardon. It was a humble plea after the mistake, and it opened the door to mercy."
        ),
        QAItem(
            question=f"Why did {p.villager} choose not to stay angry?",
            answer=f"{p.villager} saw the shame in {p.wrongdoer}'s face and chose mercy instead. The broken thing mattered, but the chance to mend the wrong mattered more."
        ),
        QAItem(
            question="What was the twist at the end?",
            answer=f"{twist.clue} {twist.reveal} That surprise turned the sorrow into something useful and made the moral feel true."
        ),
        QAItem(
            question=f"What changed about the damaged {good.label_word}?",
            answer=f"It was damaged at first, but the final turn added value and meaning back to it. The story ends with repair rather than waste."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is pardon?",
            answer="Pardon means to forgive someone and let them begin again after doing wrong."
        ),
        QAItem(
            question="What is mercy?",
            answer="Mercy is kindness shown to someone who has made a mistake or caused harm."
        ),
        QAItem(
            question="Why can a broken thing still matter in a story?",
            answer="A broken thing can matter because it helps teach a lesson about choices, repair, and how people treat each other."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} ({e.type:7}) meters={e.meters} memes={e.memes} role={e.role}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


VILLAGERS = {
    "mara": "girl",
    "jon": "boy",
    "elsa": "girl",
    "tobin": "boy",
}
WRONGDOERS = {
    "pip": "boy",
    "lena": "girl",
    "orin": "boy",
    "sela": "girl",
}
GOODS = {
    "bell": Good(id="bell", label="small bell", phrase="a small bell", kind="bell", value=1.0, tags={"bell"}),
    "loaf": Good(id="loaf", label="round loaf", phrase="a round loaf", kind="bread", value=1.0, tags={"bread"}),
    "cloak": Good(id="cloak", label="wool cloak", phrase="a wool cloak", kind="cloth", value=1.0, tags={"cloth"}),
}
TWISTS_BY_ID = {
    "hidden_loaf": Twist(id="hidden_loaf", kind="miller", clue="Behind the mill, a second oven was still warm.", reveal="It held a fresh loaf that the helper offered to share.", gift="the village ate bread together"),
    "lost_ring": Twist(id="lost_ring", kind="widow", clue="In the river grass, something bright was glinting.", reveal="It was the villager's own ring, found again after the apology.", gift="the lost ring came back to its owner"),
    "stolen_bell": Twist(id="stolen_bell", kind="priest", clue="In the chapel yard, the cracked bell rope had been tied off.", reveal="The helper had a spare bell for the feast and lent it gladly.", gift="the feast still rang with music"),
}
TWISTS = TWISTS_BY_ID
HELPERS = {"miller": Entity(id="Milo", type="man"), "widow": Entity(id="Nessa", type="woman"), "priest": Entity(id="Father Reed", type="man")}
HELPERS_BY_KIND = {"miller": "Milo", "widow": "Nessa", "priest": "Father Reed"}
CURATED = [
    StoryParams(villager="mara", villager_type="girl", wrongdoer="pip", wrongdoer_type="boy", harmed_good="bell", harmed_label="small bell", harmed_kind="bell", helper="Milo", helper_type="man", twist="hidden_loaf"),
    StoryParams(villager="jon", villager_type="boy", wrongdoer="sela", wrongdoer_type="girl", harmed_good="cloak", harmed_label="wool cloak", harmed_kind="cloth", helper="Nessa", helper_type="woman", twist="lost_ring"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for k in VILLAGERS:
        lines.append(asp.fact("villager", k))
    for k in WRONGDOERS:
        lines.append(asp.fact("wrongdoer", k))
    for k in GOODS:
        lines.append(asp.fact("good", k))
    for k in TWISTS_BY_ID:
        lines.append(asp.fact("twist", k))
    return "\n".join(lines)


ASP_RULES = r"""
valid(V,W,G,T) :- villager(V), wrongdoer(W), good(G), twist(T).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    print("OK: ASP parity" if ok else "MISMATCH: ASP parity")
    sample = generate(resolve_params(argparse.Namespace(villager=None, wrongdoer=None, good=None, twist=None), random.Random(7)))
    if not sample.story.strip():
        print("MISMATCH: empty story")
        return 1
    print("OK: generate smoke test")
    return 0 if ok else 1


def generate(params: StoryParams) -> StorySample:
    if params.villager not in VILLAGERS:
        raise StoryError("unknown villager")
    if params.wrongdoer not in WRONGDOERS:
        raise StoryError("unknown wrongdoer")
    if params.harmed_good not in GOODS:
        raise StoryError("unknown good")
    if params.twist not in TWISTS_BY_ID:
        raise StoryError("unknown twist")
    world = _setup_world(params)
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for combo in combos:
            print(combo)
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random((args.seed or 0) + i))
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
