#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/journal_magic_lesson_learned_fairy_tale.py
===========================================================================

A small standalone storyworld in a fairy-tale style about a child, a magic
journal, a wish gone a bit sideways, and a lesson learned. The simulated domain
is intentionally tiny: a young character finds or receives a journal that can
do one kind of magic, makes a choice with it, meets a gentle consequence, and
learns to use the magic more wisely.

The world keeps state in physical meters and emotional memes, uses forward
rules to drive the prose, and provides QA plus a declarative ASP twin.

Base seed idea
--------------
A child finds a journal that can make one wish real. The magic works, but the
first wish is careless. A calm helper shows how to fix the trouble, and the
child learns a lesson: magic should be used kindly and carefully.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/journal_magic_lesson_learned_fairy_tale.py
    python storyworlds/worlds/gpt-5.4-mini/journal_magic_lesson_learned_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/journal_magic_lesson_learned_fairy_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/journal_magic_lesson_learned_fairy_tale.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    magical: bool = False
    fragile: bool = False
    can_write: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "witch"}
        male = {"boy", "father", "dad", "man", "king", "wizard"}
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
    mood: str
    has_tree: bool = False
    has_well: bool = False

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
    wish: str
    effect: str
    risk: str
    lesson: str
    sense: int
    power: int
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
class Charm:
    id: str
    label: str
    help_text: str
    safe: bool = True
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    jar = world.entities.get("journal")
    if not jar or jar.meters["glowing"] < THRESHOLD:
        return out
    sig = ("spill", "journal")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for c in world.characters():
        c.memes["wonder"] += 1
    out.append("__glow__")
    return out


def _r_regret(world: World) -> list[str]:
    out: list[str] = []
    for c in world.characters():
        if c.meters["mistake"] < THRESHOLD:
            continue
        sig = ("regret", c.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        c.memes["worry"] += 1
        out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("spill", "magic", _r_spill), Rule("regret", "social", _r_regret)]


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


def reasonable_spell(spell: Spell) -> bool:
    return spell.sense >= SENSE_MIN


def spell_for_setting(setting: Setting) -> Spell:
    return SPELLS["wish"]


def predict_magic(world: World, spell: Spell) -> dict:
    sim = world.copy()
    _do_spell(sim, sim.get("journal"), spell, narrate=False)
    return {
        "glowing": sim.get("journal").meters["glowing"] >= THRESHOLD,
        "mistake": any(c.meters["mistake"] >= THRESHOLD for c in sim.characters()),
    }


def _do_spell(world: World, journal: Entity, spell: Spell, narrate: bool = True) -> None:
    journal.meters["glowing"] += 1
    journal.meters["opened"] += 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, spell: Spell, charm: Charm,
         child_name: str = "Mira", child_gender: str = "girl",
         helper_name: str = "Grandma", helper_gender: str = "woman") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child",
                             traits=["curious"], attrs={"setting": setting.id}))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper",
                              traits=["wise", "gentle"]))
    journal = world.add(Entity(id="journal", kind="thing", type="journal", label="a velvet journal",
                               magical=True, fragile=True, can_write=True))
    world.add(Entity(id="ink", kind="thing", type="ink", label="silver ink"))
    child.memes["hope"] += 1
    child.memes["care"] += 1
    helper.memes["calm"] += 1

    world.say(
        f"In a little cottage by the whispering wood, {child.id} found {journal.label} "
        f"that shimmered like moonlight. {journal.label_word.capitalize()} was not an ordinary book; "
        f"it was a magic journal that waited for a wish."
    )
    world.say(
        f"{child.id} loved the sparkle of its pages and wanted to write one brave wish. "
        f'"I can make it happen," {child.id} whispered, with {child.pronoun("possessive")} heart thumping fast.'
    )

    world.para()
    child.memes["impulse"] += 1
    world.say(
        f"{child.id} wrote a wish in the journal: {spell.wish}. For a blink, the ink "
        f"glowed gold, and the words warmed like a tiny fireplace."
    )
    _do_spell(world, journal, spell)
    child.meters["mistake"] += 1
    world.say(
        f"At once, the spell worked a little too well. The pages rustled, the room twinkled, "
        f"and {spell.effect}."
    )

    world.para()
    if child.meters["mistake"] >= THRESHOLD:
        world.say(
            f"But then {spell.risk}. {child.id} gasped and held the journal close, suddenly not so sure."
        )
        world.say(
            f'{helper.id} came in softly and said, "Magic is a gift, dear one, but gifts need care. '
            f'{spell.lesson}"'
        )
        world.say(
            f"Together they used {charm.label}. {charm.help_text}. The glitter settled, and the journal's glow grew gentle."
        )
        child.memes["relief"] += 1
        child.memes["lesson"] += 1
        helper.memes["pride"] += 1
    world.para()
    world.say(
        f"That evening, {child.id} wrote a new line in the journal with a slower hand: "
        f'"{spell.lesson}" The cottage stayed warm, the pages stayed safe, and the magic shone kindly in the dark.'
    )

    world.facts.update(
        child=child,
        helper=helper,
        journal=journal,
        spell=spell,
        charm=charm,
        setting=setting,
        outcome="lesson_learned",
        learned=child.memes["lesson"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "cottage": Setting("cottage", "the little cottage", "cozy", has_tree=True),
    "tower": Setting("tower", "the old tower room", "high", has_well=False),
    "garden": Setting("garden", "the moonlit garden", "soft", has_tree=True, has_well=True),
}

SPELLS = {
    "wish": Spell(
        "wish",
        wish="I wish the flowers would bloom all at once",
        effect="every bud burst open with bright petals",
        risk="the whole basket of seeds shook and tumbled onto the floor",
        lesson="a good wish should be small and kind",
        sense=3,
        power=2,
        tags={"magic", "wish", "bloom"},
    ),
    "light": Spell(
        "light",
        wish="I wish the lantern would glow for our reading",
        effect="a warm light filled the room",
        risk="the light flickered too fast and scared the moths from the window",
        lesson="magic works best when it is calm and clear",
        sense=3,
        power=2,
        tags={"magic", "light"},
    ),
    "rain": Spell(
        "rain",
        wish="I wish the garden would have a gentle rain",
        effect="a soft rain kissed the herbs and leaves",
        risk="the path puddled up and made the stones slippery",
        lesson="it is wiser to ask for gentle help than for too much at once",
        sense=2,
        power=1,
        tags={"magic", "rain"},
    ),
}

CHARMS = {
    "ribbon": Charm("ribbon", "a blue ribbon bookmark", "They tied the ribbon to mark the page and breathe slowly.", tags={"bookmark"}),
    "cover": Charm("cover", "a soft cloth cover", "They covered the journal so the glow would rest.", tags={"cover"}),
    "inkwell": Charm("inkwell", "a tiny inkwell lid", "They closed the inkwell and pressed the page flat.", tags={"ink"}),
}

GIRL_NAMES = ["Mira", "Luna", "Eliza", "Rose", "Nina", "Hazel", "Ivy"]
BOY_NAMES = ["Theo", "Felix", "Owen", "Rowan", "Jasper", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for sp in SPELLS:
            for ch in CHARMS:
                combos.append((s, sp, ch))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    spell: str
    charm: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c, h, sp = f["child"], f["helper"], f["spell"]
    return [
        f'Write a fairy-tale story for a 3-to-5-year-old that includes the word "journal" and a touch of magic.',
        f"Tell a gentle story where {c.id} writes a wish in a magic journal, something surprising happens, and {h.id} helps with a lesson learned.",
        f'Write a story in a fairy-tale style about a journal, a spell, and the lesson "{sp.lesson}".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c, h, j, sp, ch = f["child"], f["helper"], f["journal"], f["spell"], f["charm"]
    qa = [
        ("Who is the story about?",
         f"It is about {c.id}, who found a magic journal, and {h.id}, who helped with a kind lesson."),
        ("What did the child write in the journal?",
         f"{c.id} wrote, “{sp.wish}.” The wish was magical, but it needed care."),
        ("What happened when the wish was written?",
         f"{sp.effect}. That was the happy part, but the magic also brought a small problem along with it."),
        ("How did the helper respond?",
         f"{h.id} stayed calm and explained that {sp.lesson}. Then {ch.label} helped settle the glow so the journal could be used safely."),
        ("What did the child learn?",
         f"{c.id} learned that {sp.lesson}. By the end, the child wrote more carefully and the magic felt gentle instead of wild."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["spell"].tags) | set(f["charm"].tags) | {"magic", "journal"}
    out = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(items)
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
        if e.magical:
            bits.append("magical=True")
        if e.fragile:
            bits.append("fragile=True")
        if e.can_write:
            bits.append("can_write=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("cottage", "wish", "cover", "Mira", "girl", "Grandma", "woman"),
    StoryParams("garden", "light", "ribbon", "Theo", "boy", "Aunt Hazel", "woman"),
    StoryParams("tower", "rain", "inkwell", "Luna", "girl", "King Rowan", "man"),
]


def explain_rejection(spell: Spell) -> str:
    return f"(No story: the spell '{spell.id}' is not reasonable enough for this tiny tale.)"


def outcome_of(params: StoryParams) -> str:
    return "lesson_learned"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, sp in SPELLS.items():
        lines.append(asp.fact("spell", sid))
        lines.append(asp.fact("sense", sid, sp.sense))
        lines.append(asp.fact("power", sid, sp.power))
    for cid in CHARMS:
        lines.append(asp.fact("charm", cid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(S) :- spell(S), sense(S, N), sense_min(M), N >= M.
valid(Se, Sp, Ch) :- setting(Se), spell(Sp), charm(Ch), sensible(Sp).
"""


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(s for (s,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    if set(asp_sensible()) == {s for s, sp in SPELLS.items() if sp.sense >= SENSE_MIN}:
        print("OK: sensible spells match.")
    else:
        rc = 1
        print("MISMATCH in sensible spells.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, spell=None, charm=None,
                                                            child_name=None, child_gender=None,
                                                            helper_name=None, helper_gender=None),
                                         random.Random(777)))
        _ = sample.story
        print("OK: smoke-tested normal generation.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about a magic journal and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["woman", "man"])
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
    if args.spell and not reasonable_spell(SPELLS[args.spell]):
        raise StoryError(explain_rejection(SPELLS[args.spell]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.spell is None or c[1] == args.spell)
              and (args.charm is None or c[2] == args.charm)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, spell, charm = rng.choice(sorted(combos))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(["Grandma", "Aunt Hazel", "The Wise Oak", "The Good Queen"])
    return StoryParams(setting, spell, charm, child_name, gender, helper_name, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SPELLS[params.spell], CHARMS[params.charm],
                 params.child_name, params.child_gender, params.helper_name, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible spells: {', '.join(asp_sensible())}\n")
        for s, sp, ch in asp_valid_combos():
            print(f"  {s:8} {sp:8} {ch}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
