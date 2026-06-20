#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ranch_phenomenon_warm_sharing_cautionary_rhyme_bedtime.py
========================================================================================

A small bedtime storyworld about a ranch, a curious phenomenon, warm sharing, and
a cautionary rhyme.

This world builds a tiny simulated scene:
- a ranch at dusk,
- a warm phenomenon that can be harmless or risky,
- a child who wants to investigate it,
- a cautious sibling or parent who shares a safer idea,
- a bedtime ending with rhyme, comfort, and a clear change in state.

The core premise is that something warm and strange appears on the ranch at night.
If the children get too close, the phenomenon can sting or make the night uneasy.
A cautious helper notices the risk, offers a shared safer choice, and the story
ends with a cozy bedtime image that proves what changed.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/ranch_phenomenon_warm_sharing_cautionary_rhyme_bedtime.py
    python storyworlds/worlds/gpt-5.4-mini/ranch_phenomenon_warm_sharing_cautionary_rhyme_bedtime.py --all
    python storyworlds/worlds/gpt-5.4-mini/ranch_phenomenon_warm_sharing_cautionary_rhyme_bedtime.py --qa --json
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.meters.setdefault("warmth", 0.0)
        self.meters.setdefault("risk", 0.0)
        self.meters.setdefault("safe", 0.0)
        self.memes.setdefault("curiosity", 0.0)
        self.memes.setdefault("caution", 0.0)
        self.memes.setdefault("comfort", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    bedtime_detail: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Phenomenon:
    id: str
    noun: str
    glow: str
    warmth: int
    risk: int
    rhyme: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class SharingItem:
    id: str
    noun: str
    phrase: str
    warm_help: str
    comfort: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class CautionMove:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_warmth(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["warmth"] < THRESHOLD:
            continue
        sig = ("warmth", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "barn" in world.entities:
            world.get("barn").meters["cozy"] = world.get("barn").meters.get("cozy", 0.0) + 1
        out.append("__warm__")
    return out


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["risk"] < THRESHOLD:
            continue
        sig = ("risk", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in world.characters():
            kid.memes["uneasy"] = kid.memes.get("uneasy", 0.0) + 1
        out.append("__risk__")
    return out


CAUSAL_RULES = [Rule("warmth", "physical", _r_warmth), Rule("risk", "social", _r_risk)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def is_risky(phen: Phenomenon) -> bool:
    return phen.risk >= 2


def best_caution() -> CautionMove:
    return max(CAUTION_MOVES.values(), key=lambda c: c.sense)


def sensible_cautions() -> list[CautionMove]:
    return [c for c in CAUTION_MOVES.values() if c.sense >= 2]


def outcome_of(params: "StoryParams") -> str:
    if params.calmer and params.caution == "listen":
        return "shared"
    return "contained" if CAUTION_MOVES[params.caution].power >= PHENOMENA[params.phenomenon].risk + params.delay else "spooked"


def predict(world: World, phen: Phenomenon) -> dict:
    sim = world.copy()
    _touch_phenomenon(sim, sim.get("phen"), phen, narrate=False)
    return {"risk": sim.get("phen").meters["risk"], "warmth": sim.get("phen").meters["warmth"]}


def _touch_phenomenon(world: World, child: Entity, phen: Phenomenon, narrate: bool = True) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    child.meters["warmth"] += phen.warmth
    child.meters["risk"] += phen.risk
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"At {setting.place} on a hush-hush evening, {child.id} and {helper.id} "
        f"kept their voices soft. {setting.bedtime_detail}"
    )


def discover(world: World, child: Entity, phen: Phenomenon) -> None:
    world.say(
        f"Then a {phen.noun} began to shimmer near the fence. It gave off a "
        f"{phen.glow}, warm as toast, and the whole yard felt like a tiny wonder."
    )


def want_to_share(world: World, child: Entity, item: SharingItem) -> None:
    world.say(
        f'{child.id} reached for {item.phrase}. "If we share a warm snack, the night '
        f"will feel less strange," f' {child.id} said.'
    )


def caution(world: World, helper: Entity, child: Entity, phen: Phenomenon, move: CautionMove) -> None:
    pred = predict(world, phen)
    helper.memes["caution"] = helper.memes.get("caution", 0.0) + 1
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f'{helper.id} touched {helper.pronoun("possessive")} chin and whispered, '
        f'"Careful, {child.id}. That warm {phen.noun} is not a bedtime toy; '
        f'it can make the dark feel too sharp."'
    )
    world.say(f'Then {helper.id} added a little rhyme: "{phen.rhyme}"')


def share(world: World, child: Entity, helper: Entity, item: SharingItem) -> None:
    child.meters["safe"] += 1
    helper.meters["safe"] += 1
    child.memes["comfort"] += 1
    helper.memes["comfort"] += 1
    world.say(
        f"{helper.id} shared {item.phrase}, and {child.id} scooted closer to the "
        f"warm lamp instead of the strange glow."
    )
    world.say(
        f"{item.warm_help} The two of them shared the quiet treat, and the ranch "
        f"felt gentle again."
    )


def risk_touch(world: World, child: Entity, helper: Entity, phen: Phenomenon) -> None:
    child.meters["risk"] += phen.risk
    child.memes["uneasy"] = child.memes.get("uneasy", 0.0) + 1
    world.say(
        f"{child.id} leaned in anyway, and the warm thing hummed brighter. "
        f"For a moment the night went tingly and uneasy."
    )


def calm_fix(world: World, helper: Entity, move: CautionMove, phen: Phenomenon) -> None:
    world.say(
        f"At once, {helper.id} used {move.text}."
        f" The warm shimmer settled down, and the fence line stopped buzzing."
    )
    world.say(
        f"{move.qa_text} After that, the ranch only held a soft glow, not a scare."
    )


def bedtime(world: World, child: Entity, helper: Entity, item: SharingItem, setting: Setting) -> None:
    world.say(
        f"Before sleep, {child.id} tucked {item.noun} beside the pillow and "
        f"{helper.id} drew the curtains at {setting.place}."
    )
    world.say(
        f"Under the blankets, they smiled at the rhyme and the shared warmth: "
        f"quiet ranch, safe and snug, with a little light and a loving hug."
    )


def tell(setting: Setting, phen: Phenomenon, item: SharingItem, move: CautionMove,
         child_name: str = "Mira", child_gender: str = "girl",
         helper_name: str = "Nina", helper_gender: str = "girl",
         calm: str = "listens", delay: int = 0, calmer: bool = True) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    barn = world.add(Entity(id="barn", type="place", label="the barn"))
    phen_ent = world.add(Entity(id="phen", type="phenomenon", label=phen.noun))
    child.memes["curiosity"] = 2
    helper.memes["caution"] = 2
    intro(world, child, helper, setting)
    discover(world, child, phen)
    world.para()
    want_to_share(world, child, item)
    caution(world, helper, child, phen, move)
    shared = calmer and calm == "listens"
    if shared:
        share(world, child, helper, item)
        outcome = "shared"
    else:
        risk_touch(world, child, helper, phen)
        if move.power >= phen.risk + delay:
            world.para()
            calm_fix(world, helper, move, phen)
            outcome = "contained"
        else:
            world.para()
            world.say("The glow faded only after a very long, nervous minute.")
            world.say("They tiptoed back to bed and remembered the rhyme all night.")
            outcome = "spooked"
    world.para()
    bedtime(world, child, helper, item, setting)
    world.facts.update(
        child=child, helper=helper, setting=setting, phenomenon=phen, item=item, move=move,
        outcome=outcome, shared=shared, delay=delay,
    )
    return world


SETTINGS = {
    "ranch": Setting("ranch", "the ranch", "The horses were quiet, and even the gate looked sleepy."),
    "barn": Setting("barn", "the barn", "Hay smelled warm, and the lantern light made soft yellow squares."),
}

PHENOMENA = {
    "glow": Phenomenon("glow", "glow", "golden and soft", 1, 1, "Warm glow, stay slow."),
    "lantern": Phenomenon("lantern", "lantern flicker", "like honey light", 1, 2, "Warm lantern, no sharp banter."),
    "mystery": Phenomenon("mystery", "mystery shine", "like a small sun", 2, 2, "Warm mystery, take it easy."),
}

SHARING = {
    "tea": SharingItem("tea", "cup of tea", "a cup of tea", "They sipped slowly and felt cozy.", "cozy"),
    "blanket": SharingItem("blanket", "blanket", "a quilted blanket", "It wrapped around both shoulders like a hug.", "warm"),
    "cookies": SharingItem("cookies", "plate of cookies", "two little cookies", "They crunched softly and shared every crumb.", "sweet"),
}

CAUTION_MOVES = {
    "listen": CautionMove("listen", 3, 3, "turning down the lantern and stepping back", "stepped back too late", "The caution helped them choose the safe side"),
    "cover": CautionMove("cover", 2, 2, "covering the strange glow with a metal pail", "covered it, but the glow kept buzzing", "The cover kept the warm thing from growing"),
    "call": CautionMove("call", 3, 4, "calling a grown-up from the porch", "called too late", "The grown-up came quickly and made things calm"),
}

CHILD_NAMES = ["Mira", "Luna", "Eli", "Nora", "Ivy", "Theo", "Rose", "Finn"]
HELPER_NAMES = ["Nina", "June", "Pa", "Mae", "Lily", "Owen", "Ada", "Sam"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    phenomenon: str
    sharing: str
    caution: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    calm: str
    delay: int = 0
    calmer: bool = True
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for s in SETTINGS:
        for p in PHENOMENA:
            for sh in SHARING:
                for c in CAUTION_MOVES:
                    if PHENOMENA[p].risk <= CAUTION_MOVES[c].power + 1:
                        out.append((s, p, sh, c))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime ranch storyworld about a warm phenomenon, sharing, and caution.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--phenomenon", choices=PHENOMENA)
    ap.add_argument("--sharing", choices=SHARING)
    ap.add_argument("--caution", choices=CAUTION_MOVES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
    ap.add_argument("--calmer", action="store_true")
    ap.add_argument("--no-calmer", action="store_true")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.caution and CAUTION_MOVES[args.caution].sense < 2:
        raise StoryError("The caution must be a sensible one for this bedtime story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.phenomenon is None or c[1] == args.phenomenon)
              and (args.sharing is None or c[2] == args.sharing)
              and (args.caution is None or c[3] == args.caution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, phenomenon, sharing, caution = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    helper_name = args.helper or rng.choice([n for n in HELPER_NAMES if n != child_name])
    calm = "listens" if args.calmer or not args.no_calmer else "wanders"
    delay = 0 if args.delay is None else args.delay
    calmer = not args.no_calmer
    return StoryParams(setting, phenomenon, sharing, caution, child_name, child_gender, helper_name, helper_gender, calm, delay, calmer)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PHENOMENA[params.phenomenon], SHARING[params.sharing], CAUTION_MOVES[params.caution],
                 params.child_name, params.child_gender, params.helper_name, params.helper_gender, params.calm, params.delay, params.calmer)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for children about a {f["setting"].place} and a warm {f["phenomenon"].noun} that includes the word "ranch".',
        f"Tell a cautionary rhyming story where {f['child'].id} wants to share near a warm mystery on the ranch, but {f['helper'].id} helps choose the safer way.",
        f'Write a gentle rhyme about sharing at bedtime that includes the words "phenomenon" and "warm".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, phen, item = f["child"], f["helper"], f["phenomenon"], f["item"]
    out = [
        ("Who is the story about?", f"It is about {child.id} and {helper.id}, who were together at the ranch. The warm little problem made them choose carefully."),
        ("What did the child want to do?", f"{child.id} wanted to share {item.phrase} and go nearer to the warm {phen.noun}. {child.id} thought it might be a cozy bedtime game."),
        ("What did the helper do?", f"{helper.id} warned {child.id} with a rhyme and helped the night stay safe. That gentle warning changed the ending."),
    ]
    if f["outcome"] == "shared":
        out.append(("How did the story end?", f"They shared {item.phrase}, listened to the cautionary rhyme, and went to sleep feeling cozy. The ranch stayed peaceful and warm in a safe way."))
    elif f["outcome"] == "contained":
        out.append(("How did the story end?", f"The warm {phen.noun} was calmed down, and then they went to bed with {item.noun} close by. The ending shows that a careful choice kept the ranch quiet."))
    else:
        out.append(("How did the story end?", f"They backed away and remembered the rhyme because the warm {phen.noun} felt too strange. They were safe, but the night stayed nervous for a while."))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["phenomenon"].tags) | set(world.facts["item"].tags)
    qa: list[tuple[str, str]] = []
    if "warm" in tags or True:
        qa.append(("What does warm mean?", "Warm means pleasantly hot, like a cozy blanket or a mug of cocoa. It feels nice when it is safe and gentle."))
    qa.append(("What is a ranch?", "A ranch is a place where people keep animals like horses or cows, and there is lots of open space."))
    qa.append(("What is a phenomenon?", "A phenomenon is something unusual that people notice, like a strange light or a mysterious sound."))
    qa.append(("Why do people share at bedtime?", "Sharing at bedtime can help everyone feel safe, calm, and close. It turns a worrisome night into a softer one."))
    return qa


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PHENOMENA.items():
        lines.append(asp.fact("phenomenon", pid))
        lines.append(asp.fact("risk", pid, p.risk))
    for sid in SHARING:
        lines.append(asp.fact("sharing", sid))
    for cid, c in CAUTION_MOVES.items():
        lines.append(asp.fact("caution", cid))
        lines.append(asp.fact("sense", cid, c.sense))
        lines.append(asp.fact("power", cid, c.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(C) :- caution(C), sense(C,S), sense_min(M), S >= M.
valid(S,P,Sh,C) :- setting(S), phenomenon(P), sharing(Sh), sensible(C), risk(P,R), power(C, Pow), Pow + 1 >= R.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    import itertools
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        print("  only in asp:", sorted(cl - py))
        print("  only in python:", sorted(py - cl))
    sample = generate(resolve_params(argparse.Namespace(setting=None, phenomenon=None, sharing=None, caution=None, name=None, helper=None, gender=None, helper_gender=None, delay=None, calmer=False, no_calmer=False), random.Random(7)))
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: generate produced empty story.")
    else:
        print("OK: generate smoke test produced a story.")
    return rc


def explain_rejection() -> str:
    return "The chosen warmth-and-caution combination does not make a bedtime-safe story."


CURATED = [
    StoryParams("ranch", "glow", "blanket", "listen", "Mira", "girl", "Nina", "girl", "listens", 0, True),
    StoryParams("barn", "mystery", "cookies", "call", "Eli", "boy", "Pa", "boy", "listens", 0, True),
    StoryParams("ranch", "lantern", "tea", "cover", "Rose", "girl", "Mae", "girl", "listens", 1, True),
]


def world_from_params(params: StoryParams) -> World:
    return tell(SETTINGS[params.setting], PHENOMENA[params.phenomenon], SHARING[params.sharing], CAUTION_MOVES[params.caution],
                params.child_name, params.child_gender, params.helper_name, params.helper_gender, params.calm, params.delay, params.calmer)


def generate(params: StoryParams) -> StorySample:
    world = world_from_params(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world),
                       story_qa=[QAItem(q, a) for q, a in story_qa(world)],
                       world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)], world=world)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.caution and CAUTION_MOVES[args.caution].sense < 2:
        raise StoryError("Choose a more sensible caution move.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.phenomenon is None or c[1] == args.phenomenon)
              and (args.sharing is None or c[2] == args.sharing)
              and (args.caution is None or c[3] == args.caution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, phenomenon, sharing, caution = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    helper_name = args.helper or rng.choice([n for n in HELPER_NAMES if n != child_name])
    calm = "listens" if args.calmer or not args.no_calmer else "wanders"
    return StoryParams(setting, phenomenon, sharing, caution, child_name, child_gender, helper_name, helper_gender, calm, 0 if args.delay is None else args.delay, not args.no_calmer)


if __name__ == "__main__":
    main()
