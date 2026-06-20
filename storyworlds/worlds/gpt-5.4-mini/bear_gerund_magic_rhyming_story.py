#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bear_gerund_magic_rhyming_story.py
==================================================================

A small, self-contained storyworld for a magical, rhyming bear tale.

Core premise:
- A child bear is happily doing a gerund activity in a cozy place.
- The activity needs magical help, but a small spell goes wrong.
- A calm helper fixes it with a better bit of magic.
- The ending proves the world changed: the bear keeps playing, now with safe magic.

The world is intentionally compact: one domain, a few entities, a forward
simulation, grounded QA, and an inline ASP twin for parity checks.
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)
    magic: bool = False
    sparkly: bool = False

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"glow": 0.0, "mess": 0.0, "fix": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "trust": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "bear", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



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
    rhyme: str
    mood: str
    light: str
    afford_magic: bool = True

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
class Activity:
    id: str
    gerund: str
    verb: str
    rhyme: str
    needs_magic: bool
    mess_kind: str

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
class Spell:
    id: str
    name: str
    rhyme: str
    power: int
    safe: bool
    text: str
    fail: str
    qa_text: str

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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

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
class Rule:
    name: str
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


def _r_worry(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.role != "bear" or e.meters["mess"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_glow(world: World) -> list[str]:
    out = []
    if "spell" not in world.entities:
        return out
    spell = world.get("spell")
    bear = world.get("bear")
    if bear.meters["glow"] < THRESHOLD:
        return out
    sig = ("glow", spell.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if spell.safe:
        world.get("room").meters["glow"] += 1
        out.append("__glow__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("glow", _r_glow)]


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


def predict_spell(world: World, spell: Spell) -> dict:
    sim = world.copy()
    sim.get("bear").meters["glow"] += 1
    if spell.safe:
        sim.get("room").meters["glow"] += 1
    return {"room_glow": sim.get("room").meters["glow"], "bear_worry": sim.get("bear").memes["worry"]}


def tell(setting: Setting, activity: Activity, spell: Spell, helper: Entity, bear_name: str, helper_name: str) -> World:
    world = World(setting)
    bear = world.add(Entity(id=bear_name, kind="character", type="bear", role="bear", traits=["small", "sweet"]))
    guide = world.add(Entity(id=helper_name, kind="character", type="girl", role="helper", traits=["calm", "kind"]))
    room = world.add(Entity(id="room", type="room", label="the room"))
    wand = world.add(Entity(id="wand", type="thing", label=spell.name, magic=True))
    world.add(Entity(id="sparkle", type="thing", label="the sparkle", sparkly=True))

    bear.memes["joy"] += 1
    guide.memes["trust"] += 1

    world.say(
        f"In {setting.place}, {bear.id} was {activity.gerund}, as cozy as could be. "
        f"{setting.rhyme}"
    )
    world.say(
        f"{bear.id} loved the {setting.mood} little show, and {bear.pronoun()} kept it all in a row."
    )

    world.para()
    world.say(
        f"But {activity.rhyme} needed a twinkle of light, and the dark was a frown in the hush of night."
    )
    bear.meters["glow"] += 1

    world.say(
        f'"Let\'s try {spell.name}," said {bear.id} with a grin. "{spell.rhyme}"'
    )
    if not setting.afford_magic or not activity.needs_magic:
        raise StoryError("This story needs a magical activity in a place where magic can matter.")

    pred = predict_spell(world, spell)
    world.facts["predicted_room_glow"] = pred["room_glow"]

    if not spell.safe:
        raise StoryError("Unsafe spells are refused in this child-facing world.")

    if pred["room_glow"] > 0:
        world.say(f"{helper.id} nodded and lifted {helper.pronoun('possessive')} hand.")
    else:
        world.say(f"{helper.id} frowned, then smiled. {helper.id} knew a kinder plan.")

    world.get("spell")  # noqa: B018
    world.entities["spell"] = Entity(id="spell", type="spell", label=spell.name, magic=True)
    world.get("spell").meters["glow"] = 0.0
    world.get("spell").memes["trust"] = 1.0

    world.para()
    world.get("spell").meters["glow"] += 1
    if spell.power >= 1:
        world.get("room").meters["glow"] += 1
        world.get("bear").meters["glow"] = 0.0
        propagate(world, narrate=False)
        world.say(
            f"{spell.text.replace('{setting}', setting.place)}. "
            f"The room went bright, and the shadows lost their fight."
        )
        world.say(
            f"{helper.id} laughed, and {bear.id} clapped too; the magic was gentle, neat, and true."
        )
        ending = "bright"
    else:
        world.get("room").meters["glow"] = 0.0
        world.say(
            f"{spell.fail.replace('{setting}', setting.place)}. "
            f"So {helper.id} used a softer trick to do."
        )
        ending = "soft"

    world.para()
    world.say(
        f"Now {bear.id} kept {activity.verb} in a happy, safe way, with a glow that stayed and brightened the day."
    )
    world.say(
        f"{setting.light} shone over paws and floor, and {bear.id} sang rhymes for one minute more."
    )

    world.facts.update(
        bear=bear, helper=guide, room=room, wand=wand, spell=world.get("spell"),
        activity=activity, setting=setting, outcome=ending
    )
    return world


SETTINGS = {
    "cottage": Setting("cottage", "the cottage", "A candle? No, a tinkle and twinkle in the cottage", "warm", "Moonbeams"),
    "glade": Setting("glade", "the moonlit glade", "In the glade, the leaves all swayed", "blue", "Starlight"),
    "attic": Setting("attic", "the old attic", "Up in the attic, soft dust danced", "dusty", "Lanternlight"),
}

ACTIVITIES = {
    "bear-gerund": Activity("bear-gerund", "beary-bouncing", "bounce", "For bear-gerund fun, the shadows spun", True, "glow"),
    "bear-dreaming": Activity("bear-dreaming", "bear-dreaming", "dream", "Dreams can gleam when bears daydream", True, "glow"),
    "bear-dancing": Activity("bear-dancing", "bear-dancing", "dance", "When bears dance, the night gets a chance", True, "glow"),
}

SPELLS = {
    "moon-chime": Spell("moon-chime", "Moon Chime", "A moon chime can shimmer, a moon chime can sing", 1, True,
                        "The Moon Chime shimmered across {setting}", "The Moon Chime fizzled before it could ring",
                        "used the Moon Chime to make the room shimmer"),
    "star-bell": Spell("star-bell", "Star Bell", "A star bell can glow, and a star bell can go", 1, True,
                       "The Star Bell lit the way across {setting}", "The Star Bell dimmed and would not start",
                       "rang the Star Bell to bring a soft glow"),
    "kind-lantern": Spell("kind-lantern", "Kind Lantern", "A kind lantern will gleam, like a sweet little dream", 1, True,
                          "The Kind Lantern gave {setting} a kind, gold gleam", "The Kind Lantern stayed still as a stone",
                          "lifted the Kind Lantern for a gold gleam"),
}

HELPER = Entity(id="Mina", kind="character", type="girl", role="helper")


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, a, sp) for s in SETTINGS for a in ACTIVITIES for sp in SPELLS if SETTINGS[s].afford_magic and ACTIVITIES[a].needs_magic]


@dataclass
@dataclass
class StoryParams:
    setting: str
    activity: str
    spell: str
    bear_name: str
    helper_name: str
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


KNOWLEDGE = {
    "bear": [("What is a bear?",
              "A bear is a big furry animal. In stories, bears can be gentle, playful, and curious.")],
    "magic": [("What is magic in a story?",
               "Magic is pretend story power that can make surprising things happen, like a glow or a sparkle.")],
    "rhyming": [("What is rhyming?",
                  "Rhyming means words sound alike at the end, like light and night.")],
    "glow": [("What does glow mean?",
              "Glow means to shine with a soft light, not a loud flash.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming magical story for a young child that includes "{f["activity"].id}" and the phrase "bear-gerund".',
        f"Tell a cozy story where {f['bear'].id} is {f['activity'].gerund} and uses magic with {f['helper'].id} in {f['setting'].place}.",
        f'Write a gentle bear tale with a magic fix, soft rhymes, and a happy ending that shows the glow changed the room.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    bear, helper, act, setting = f["bear"], f["helper"], f["activity"], f["setting"]
    return [
        QAItem(f"Who is the story about?", f"It is about {bear.id}, who was {act.gerund}, and {helper.id}, who helped with magic."),
        QAItem(f"What was {bear.id} doing?", f"{bear.id} was {act.gerund} in {setting.place}. That playful action is the heart of the story."),
        QAItem(f"How did the problem get fixed?", f"{helper.id} helped use magic to make the room glow. That gentle glow turned the dark into something warm and safe."),
        QAItem(f"How did the story end?", f"It ended with {bear.id} still playing, but now the room was bright and the magic felt kind. The ending shows the change clearly."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in ("bear", "magic", "rhyming", "glow"):
        out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.magic:
            bits.append("magic=True")
        if e.sparkly:
            bits.append("sparkly=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, _ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("cottage", "bear-gerund", "moon-chime", "Benny", "Mina"),
    StoryParams("glade", "bear-dancing", "star-bell", "Milo", "Mina"),
    StoryParams("attic", "bear-dreaming", "kind-lantern", "Pip", "Mina"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny magical rhyming bear storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--bear-name")
    ap.add_argument("--helper-name")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.activity is None or c[1] == args.activity)
              and (args.spell is None or c[2] == args.spell)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, activity, spell = rng.choice(sorted(combos))
    bear_name = args.bear_name or rng.choice(["Benny", "Bram", "Buster", "Milo", "Pip"])
    helper_name = args.helper_name or "Mina"
    return StoryParams(setting, activity, spell, bear_name, helper_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIVITIES[params.activity], SPELLS[params.spell], HELPER, params.bear_name, params.helper_name)
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


ASP_RULES = r"""
valid(S,A,P) :- setting(S), activity(A), spell(P), afford_magic(S), needs_magic(A).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("afford_magic", sid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("needs_magic", aid))
    for pid in SPELLS:
        lines.append(asp.fact("spell", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos disagree.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for row in combos:
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
