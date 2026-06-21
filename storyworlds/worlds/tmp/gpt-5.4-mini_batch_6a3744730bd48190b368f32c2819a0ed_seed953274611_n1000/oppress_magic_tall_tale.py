#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/oppress_magic_tall_tale.py
==========================================================

A standalone storyworld for a tiny tall-tale about a child, a magical nuisance,
and a clever spell that lifts the burden away.

Seed words / style:
- Word: "oppress"
- Feature: Magic
- Style: Tall tale

The world keeps a small causal model with typed entities, physical meters, and
emotional memes. A child in a big-sky place tries to do a brave deed while a
heavy magical pressure hangs over the land. A helper, a tool, and a spell can
either lift the weight or fail if the burden is too large.

This script follows the shared Storyweavers contract:
- stdlib only
- eager import of storyworlds/results.py for QAItem, StoryError, StorySample
- lazy import of storyworlds/asp.py inside ASP helpers
- build_parser, resolve_params, generate, emit, main
- --trace, --qa, --json, --asp, --verify, --show-asp, --all, -n, --seed
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
BRAVERY_INIT = 6.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    magical: bool = False
    heavy: bool = False
    helps: bool = False
    covers: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "witch"}
        male = {"boy", "father", "dad", "man", "grandfather", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


@dataclass
class Spell:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    success: str
    fail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Burden:
    id: str
    label: str
    phrase: str
    weight: int
    oppressive: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Setting:
    id: str
    place: str
    image: str
    mood: str


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
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
    apply: Callable[[World], list[str]]


def _r_pressure(world: World) -> list[str]:
    out: list[str] = []
    burden = world.get("burden")
    if burden.meters["oppressing"] < THRESHOLD:
        return out
    sig = ("pressure",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.characters():
        if kid.role == "child":
            kid.memes["fear"] += 1
            kid.memes["resolve"] += 1
    world.get("valley").meters["dimness"] += 1
    out.append("__pressure__")
    return out


CAUSAL_RULES = [Rule("pressure", _r_pressure)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def burden_at_risk(setting: Setting, burden: Burden) -> bool:
    return burden.oppressive and "valley" in setting.id


def sensible_spells() -> list[Spell]:
    return [s for s in SPELLS.values() if s.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid in SETTINGS:
        for bid, b in BURDENS.items():
            for spid, sp in SPELLS.items():
                if burden_at_risk(SETTINGS[sid], b) and sp.sense >= SENSE_MIN:
                    combos.append((sid, bid, spid))
    return combos


def spell_wins(spell: Spell, burden: Burden, delay: int) -> bool:
    return spell.power >= burden.weight + delay


def predict(world: World, burden_id: str, spell_id: str) -> dict:
    sim = world.copy()
    burden = sim.get("burden")
    spell = SPELLS[spell_id]
    burden.meters["oppressing"] += 1
    if spell.power >= burden.weight:
        burden.meters["lifted"] += 1
    return {"oppressing": burden.meters["oppressing"] >= THRESHOLD, "dimness": sim.get("valley").meters["dimness"]}


def start(world: World, child: Entity, elder: Entity, setting: Setting, burden: Burden) -> None:
    child.memes["wonder"] += 1
    elder.memes["calm"] += 1
    world.say(
        f"In {setting.place}, where the sky was as wide as a wagon road, {child.id} and {elder.id} stood beneath {setting.image}."
    )
    world.say(
        f"All day long, {burden.phrase} seemed to oppress the meadow, and even the crows flew low."
    )


def desire(world: World, child: Entity, spell: Spell) -> None:
    child.memes["bravery"] += 1
    world.say(
        f'{child.id} raised {child.pronoun("possessive")} chin. "I know a way," {child.pronoun()} said. '
        f'"{spell.phrase} ought to do the trick."'
    )


def warn(world: World, elder: Entity, child: Entity, burden: Burden, spell: Spell) -> None:
    pred = predict(world, burden.id, spell.id)
    if pred["oppressing"]:
        elder.memes["worry"] += 1
        world.say(
            f'{elder.id} shook {elder.pronoun("possessive")} head. "That burden is too heavy for a little spell," {elder.pronoun()} said. '
            f'"A tall tale needs a tall answer, or the oppress will keep on pressing."'
        )


def cast(world: World, child: Entity, spell: Spell, burden: Burden) -> None:
    burden.meters["oppressing"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{child.id} whispered {spell.label}, and the air answered in silver sparks.'
    )
    world.say(
        f"The spell rose like a kite in a hot wind and tugged at the burden."
    )


def resolve(world: World, elder: Entity, spell: Spell, burden: Burden, setting: Setting, happy: bool) -> None:
    if happy:
        burden.meters["oppressing"] = 0
        burden.meters["lifted"] += 1
        world.get("valley").meters["dimness"] = 0
        world.say(
            f"In a flash, {elder.label_word.capitalize()} laughed and swept {spell.label} through the air, and the spell took hold."
        )
        world.say(
            f"The weight peeled away from {setting.place}, the sky brightened, and the meadow stood up straight like a boy after a nap."
        )
        world.say(
            f"By sundown, the whole valley was singing, and {world.facts['child'].id} could see the stars blink one by one."
        )
    else:
        burden.meters["oppressing"] += 1
        world.get("valley").meters["dimness"] += 1
        world.say(
            f"The spell crackled bravely, but the burden was too great, and it only stirred the dust."
        )
        world.say(
            f"The dark still oppress-ed the valley until the grown folk fetched a stronger charm from the old stone well."
        )
        world.say(
            f"Even so, {world.facts['child'].id} learned that a brave voice is worth more than a frightened silence."
        )


def tell(setting: Setting, burden: Burden, spell: Spell, child_name: str, child_type: str, elder_name: str, elder_type: str, delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="elder"))
    world.add(Entity(id="valley", type="place", label=setting.place))
    world.add(Entity(id="burden", type="burden", label=burden.label, magical=True, heavy=True))
    world.facts["child"] = child
    world.facts["elder"] = elder
    world.facts["setting"] = setting
    world.facts["burden"] = burden
    world.facts["spell"] = spell
    world.facts["delay"] = delay

    start(world, child, elder, setting, burden)
    world.para()
    desire(world, child, spell)
    warn(world, elder, child, burden, spell)
    world.para()

    happy = spell_wins(spell, burden, delay)
    cast(world, child, spell, burden)
    resolve(world, elder, spell, burden, setting, happy)
    world.facts["outcome"] = "lifted" if happy else "failed"
    return world


SETTINGS = {
    "valley": Setting(id="valley", place="the Blue Valley", image="a silver cloud", mood="wide-open"),
    "hill": Setting(id="hill", place="Merry Hill", image="a moon-hat of mist", mood="bright"),
}

BURDENS = {
    "fog": Burden(id="fog", label="fog", phrase="a thick fog", weight=2, oppressive=True, tags={"fog", "oppress"}),
    "curse": Burden(id="curse", label="curse", phrase="a gloomy curse", weight=3, oppressive=True, tags={"curse", "oppress"}),
    "shadow": Burden(id="shadow", label="shadow", phrase="a long shadow", weight=1, oppressive=True, tags={"shadow", "oppress"}),
}

SPELLS = {
    "bell": Spell(id="bell", label="moon-bell", phrase="the moon-bell charm", power=3, sense=3,
                  success="lifted the burden clear off the meadow", fail="rang, but could not rouse the whole sky",
                  tags={"bell", "magic"}),
    "song": Spell(id="song", label="sun-song", phrase="the sun-song spell", power=2, sense=2,
                  success="made the clouds dance away", fail="quivered and faded before the dark could move",
                  tags={"song", "magic"}),
    "feather": Spell(id="feather", label="feather charm", phrase="the feather charm", power=1, sense=1,
                     success="tickled the air but never moved the weight", fail="was too little for the burden",
                     tags={"feather", "magic"}),
}

CHILD_NAMES = ["Pip", "Nell", "Bo", "Mira", "Jem", "Ada"]
ELDER_NAMES = ["Grandma Wren", "Old Mose", "Aunt June", "Uncle Ben"]


@dataclass
class StoryParams:
    setting: str
    burden: str
    spell: str
    child_name: str
    child_type: str
    elder_name: str
    elder_type: str
    delay: int = 0
    seed: Optional[int] = None


def explain_rejection(setting: Setting, burden: Burden, spell: Spell) -> str:
    if not burden_at_risk(setting, burden):
        return "(No story: this burden does not truly oppress the valley in a way the tale can address.)"
    if spell.sense < SENSE_MIN:
        return f"(No story: the {spell.label} charm is too flimsy for a tall-tale fix.)"
    return "(No story: this combination is not reasonable.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tall-tale storyworld about magic, burden, and a brave lift.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--burden", choices=BURDENS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--child-name")
    ap.add_argument("--elder-name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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
    if args.setting and args.burden and args.spell:
        s, b, sp = SETTINGS[args.setting], BURDENS[args.burden], SPELLS[args.spell]
        if not (burden_at_risk(s, b) and sp.sense >= SENSE_MIN):
            raise StoryError(explain_rejection(s, b, sp))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.burden is None or c[1] == args.burden)
              and (args.spell is None or c[2] == args.spell)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, burden, spell = rng.choice(sorted(combos))
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    elder_name = args.elder_name or rng.choice(ELDER_NAMES)
    child_type = rng.choice(["boy", "girl"])
    elder_type = "grandmother" if elder_name in {"Grandma Wren", "Aunt June"} else "grandfather"
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting=setting, burden=burden, spell=spell, child_name=child_name,
                       child_type=child_type, elder_name=elder_name, elder_type=elder_type, delay=delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story that includes the word "oppress" and a little magic charm that helps a child in {f["setting"].place}.',
        f"Tell a magical tale where {f['child'].id} sees {f['burden'].phrase} oppress the valley and learns to answer it with {f['spell'].phrase}.",
        f"Write a child-friendly tall tale about a big sky, a heavy burden, and a spell that is strong enough to lift it away.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    burden = f["burden"]
    spell = f["spell"]
    setting = f["setting"]
    outcome = f["outcome"]
    items = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {elder.id} in {setting.place}. The two of them face a magical burden together.",
        ),
        QAItem(
            question="What was oppressing the valley?",
            answer=f"{burden.phrase} was oppressing the valley. It made the meadow feel heavy and dim until the spell was tried.",
        ),
    ]
    if outcome == "lifted":
        items.append(QAItem(
            question=f"What happened when {child.id} used the magic charm?",
            answer=f"{spell.phrase} worked, and the burden lifted away. The sky brightened because the spell was strong enough for the job.",
        ))
        items.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with the valley shining again and everybody breathing easy. The burden was gone, so the town could sing under a clean, wide sky.",
        ))
    else:
        items.append(QAItem(
            question=f"Did {spell.label} work by itself?",
            answer=f"No, it did not. The burden was too heavy, so the tale needed a stronger charm before the valley could be free.",
        ))
        items.append(QAItem(
            question="How did the story end?",
            answer="It ended with a lesson about brave voices and stronger magic. The burden was still there at first, but help from the grown folk came next.",
        ))
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["burden"].tags) | set(world.facts["spell"].tags) | {"magic"}
    qas = {
        "oppress": QAItem("What does oppress mean in a story like this?", "It means to press down or weigh on something so it feels heavy, gloomy, or hard to bear."),
        "magic": QAItem("What is magic in a tall tale?", "Magic is a make-believe power that can do impossible things, like moving clouds or lifting a burden."),
        "fog": QAItem("What is fog?", "Fog is a cloud near the ground that makes the world look pale and blurry."),
        "curse": QAItem("What is a curse in a story?", "A curse is a bad spell or wish that brings trouble, gloom, or bad luck."),
        "shadow": QAItem("What is a shadow?", "A shadow is a dark shape made when something blocks the light."),
    }
    order = ["oppress", "magic", "fog", "curse", "shadow"]
    return [qas[k] for k in order if k in tags]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.magical:
            bits.append("magical")
        if e.heavy:
            bits.append("heavy")
        out.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(out)


ASP_RULES = r"""
oppressive(B) :- burden(B), heavy(B).
valid(S, B, P) :- setting(S), burden(B), spell(P), oppressive(B), spell_sensible(P).
strong_enough(P, B) :- spell(P), burden(B), power(P, Pw), weight(B, W), delay(D), Pw >= W + D.
outcome(lifted) :- chosen_spell(P), chosen_burden(B), chosen_delay(D), strong_enough(P, B), delay(D).
outcome(failed) :- chosen_spell(P), chosen_burden(B), chosen_delay(D), not strong_enough(P, B), delay(D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid, b in BURDENS.items():
        lines.append(asp.fact("burden", bid))
        if b.oppressive:
            lines.append(asp.fact("heavy", bid))
        lines.append(asp.fact("weight", bid, b.weight))
    for pid, p in SPELLS.items():
        lines.append(asp.fact("spell", pid))
        lines.append(asp.fact("power", pid, p.power))
        lines.append(asp.fact("spell_sensible", pid))
    lines.append(asp.fact("delay", 0))
    lines.append(asp.fact("delay", 1))
    lines.append(asp.fact("delay", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_spell", params.spell),
        asp.fact("chosen_burden", params.burden),
        asp.fact("chosen_delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP gate differs from Python valid_combos().")
    # smoke test ordinary generation
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, burden=None, spell=None, child_name=None, elder_name=None, delay=None), random.Random(7)))
        assert sample.story
        _ = sample.to_json()
        print("OK: generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    # outcome parity on curated and random cases
    cases = list(CURATED)
    rng = random.Random(0)
    for i in range(20):
        try:
            cases.append(resolve_params(argparse.Namespace(setting=None, burden=None, spell=None, child_name=None, elder_name=None, delay=None), random.Random(i)))
        except StoryError:
            pass
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome parity passed for {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differed.")
    return rc


def outcome_of(params: StoryParams) -> str:
    return "lifted" if spell_wins(SPELLS[params.spell], BURDENS[params.burden], params.delay) else "failed"


CURATED = [
    StoryParams(setting="valley", burden="fog", spell="bell", child_name="Pip", child_type="boy", elder_name="Grandma Wren", elder_type="grandmother", delay=0),
    StoryParams(setting="valley", burden="curse", spell="song", child_name="Nell", child_type="girl", elder_name="Old Mose", elder_type="grandfather", delay=0),
    StoryParams(setting="hill", burden="shadow", spell="feather", child_name="Bo", child_type="boy", elder_name="Aunt June", elder_type="grandmother", delay=1),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.burden not in BURDENS or params.spell not in SPELLS:
        raise StoryError("(Invalid StoryParams values.)")
    setting = SETTINGS[params.setting]
    burden = BURDENS[params.burden]
    spell = SPELLS[params.spell]
    if not burden_at_risk(setting, burden):
        raise StoryError(explain_rejection(setting, burden, spell))
    if spell.sense < SENSE_MIN:
        raise StoryError(explain_rejection(setting, burden, spell))
    world = tell(setting, burden, spell, params.child_name, params.child_type, params.elder_name, params.elder_type, params.delay)
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


def build_default_parser() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.burden} and {p.spell} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
