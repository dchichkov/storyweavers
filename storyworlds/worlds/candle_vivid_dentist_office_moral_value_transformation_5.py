#!/usr/bin/env python3
"""
Mythic dentist-office storyworld driven by misunderstanding, moral value, and
transformation. The seed tale behind the simulation is:

"In a dentist office that children call the House of Smiles, a beeswax candle
burns by the mint bowl and makes vivid shapes on the wall. A worried child
misreads one sign of the room and believes the healer means harm. By practicing
one moral value, the child lets the healer reveal the truth, the candle changes
shape, and the hurting tooth is gently restored."
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STORYWORLDS = Path(__file__).resolve().parents[1]
for base in (ROOT, STORYWORLDS):
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Misreading:
    key: str
    title: str
    omen_phrase: str
    false_belief: str
    reaction: str
    helper_action: str
    reveal: str
    tool_name: str
    compatible_virtues: tuple[str, ...]


@dataclass(frozen=True)
class Virtue:
    key: str
    label: str
    child_action: str
    speech: str
    teaching: str
    candle_change: str
    final_glow: str


@dataclass(frozen=True)
class ToothCase:
    key: str
    title: str
    symptom: str
    remedy: str
    ending_image: str
    pain_level: float
    pain_relief: float


@dataclass
class StoryParams:
    misreading: str
    virtue: str
    tooth_case: str
    hero: str
    gender: str
    healer: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    states: dict[str, str] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    misreading: Misreading
    virtue: Virtue
    tooth_case: ToothCase
    entities: dict[str, Entity]
    office_title: str = "the House of Smiles"
    events: list[str] = field(default_factory=list)
    resolved: bool = False
    final_image: str = ""
    moral: str = ""
    story: str = ""

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        lines.append(f"  office_title={self.office_title}")
        lines.append(f"  misreading={self.misreading.key}")
        lines.append(f"  virtue={self.virtue.key}")
        lines.append(f"  tooth_case={self.tooth_case.key}")
        lines.append(f"  resolved={self.resolved}")
        lines.append(f"  final_image={self.final_image or 'none'}")
        lines.append(f"  moral={self.moral or 'none'}")
        for key, entity in self.entities.items():
            lines.append(f"  [{key}] {entity.name} ({entity.kind})")
            meter_text = ", ".join(f"{k}={v:.2f}" for k, v in sorted(entity.meters.items())) or "none"
            meme_text = ", ".join(f"{k}={v:.2f}" for k, v in sorted(entity.memes.items())) or "none"
            state_text = ", ".join(f"{k}={v}" for k, v in sorted(entity.states.items())) or "none"
            lines.append(f"    meters: {meter_text}")
            lines.append(f"    memes: {meme_text}")
            lines.append(f"    states: {state_text}")
        lines.append(f"  events: {', '.join(self.events) if self.events else 'none'}")
        return "\n".join(lines)


MISREADINGS: dict[str, Misreading] = {
    "hook_shadow": Misreading(
        key="hook_shadow",
        title="hook shadow",
        omen_phrase="the silver mouth mirror threw a hook-shaped shadow across the chair",
        false_belief="the mirror was a hook meant to snatch every tooth in the mouth",
        reaction="pressed both lips closed and hid behind the chair arm",
        helper_action="tilted the mirror into the candle glow until the wall-shadow broke apart",
        reveal="the little mirror was only gathering light so the troubled tooth could be seen clearly",
        tool_name="mouth mirror",
        compatible_virtues=("truth", "courage", "patience"),
    ),
    "serpent_hiss": Misreading(
        key="serpent_hiss",
        title="serpent hiss",
        omen_phrase="the rinse hose gave a long hiss beside the mint bowl",
        false_belief="a tiny serpent spirit slept inside the hose",
        reaction="lifted both feet from the floor and would not go near the basin",
        helper_action="let mint water run through the hose until the hiss turned to bubbles in the bowl",
        reveal="the sound belonged to harmless water and air, not to any hidden serpent",
        tool_name="rinse hose",
        compatible_virtues=("patience", "courage", "kindness"),
    ),
    "mask_ogre": Misreading(
        key="mask_ogre",
        title="mask ogre",
        omen_phrase="the healer's white mask beneath the bright lamp looked like a giant face above the chair",
        false_belief="the Smile-Keeper was an ogre who ate brave words before eating tooth pain",
        reaction="whispered so softly that even the floor tiles could barely hear",
        helper_action="set the mask aside and named each shining tool in a warm voice",
        reveal="the giant face vanished at once, leaving only an ordinary dentist ready to help",
        tool_name="healer's mask",
        compatible_virtues=("truth", "courage", "kindness"),
    ),
    "echo_judgment": Misreading(
        key="echo_judgment",
        title="judging echo",
        omen_phrase="the high ceiling sent each tiny cough back as a booming echo",
        false_belief="the room judged children who admitted that a tooth hurt",
        reaction="pretended the ache was small and kept one hand over the hurting cheek",
        helper_action="clapped beneath the ceiling and laughed when the echo returned the same happy sound",
        reveal="the ceiling repeated every noise, even a laugh, and was judging no one at all",
        tool_name="echoing ceiling",
        compatible_virtues=("truth", "patience", "kindness"),
    ),
}


VIRTUES: dict[str, Virtue] = {
    "truth": Virtue(
        key="truth",
        label="truth",
        child_action="named the sore place exactly instead of hiding it",
        speech="I was afraid, and my tooth truly hurts right here.",
        teaching="Truth gives a healer something real to mend.",
        candle_change="The bent wax cleared itself into a small bright tooth around the wick.",
        final_glow="a clear tooth of wax holding a steady flame",
    ),
    "courage": Virtue(
        key="courage",
        label="courage",
        child_action="climbed into the chair even while the knees still trembled",
        speech="My knees are shaking, but I can look and listen.",
        teaching="Courage is right action taken while fear is still nearby.",
        candle_change="The flame stood straight, and the softened wax became a tiny bridge from one side of the saucer to the other.",
        final_glow="a bridge of wax under a tall brave flame",
    ),
    "patience": Virtue(
        key="patience",
        label="patience",
        child_action="counted slow breaths and listened before deciding what the signs meant",
        speech="I can wait one more breath and see what the room is really saying.",
        teaching="Patience gives truth enough time to arrive.",
        candle_change="The trembling wax grew round and calm, making a moon-cup around the wick.",
        final_glow="a moon-shaped cup of wax glowing without a shiver",
    ),
    "kindness": Virtue(
        key="kindness",
        label="kindness",
        child_action="chose a gentle voice so a younger waiting child would not borrow the fear",
        speech="I do not want my mistake to frighten anyone else.",
        teaching="Kindness turns fear away from harm and toward care.",
        candle_change="Two warm curves of wax leaned together like matching smiles on the saucer.",
        final_glow="two wax smiles holding one warm little flame",
    ),
}


TOOTH_CASES: dict[str, ToothCase] = {
    "sore_molar": ToothCase(
        key="sore_molar",
        title="sore molar",
        symptom="a deep ache in a back molar",
        remedy="cleaned the hidden sugar cave and painted it with clove-sweet medicine",
        ending_image="the back tooth felt quiet instead of stormy",
        pain_level=0.84,
        pain_relief=0.58,
    ),
    "wiggly_tooth": ToothCase(
        key="wiggly_tooth",
        title="wiggly tooth",
        symptom="a front tooth that rocked like a tiny gate in the wind",
        remedy="cooled the gum with mint cloth and showed the safe way to let the loose tooth finish its own journey",
        ending_image="the wiggly tooth rested easy and ready for its proper day",
        pain_level=0.53,
        pain_relief=0.31,
    ),
    "sugar_spot": ToothCase(
        key="sugar_spot",
        title="sugar spot",
        symptom="a bright sugar spot on a little tooth",
        remedy="polished the sweet mark away and sealed the tender place before it could deepen",
        ending_image="the little tooth shone like a pearl in a shell",
        pain_level=0.61,
        pain_relief=0.39,
    ),
}


HERO_NAMES: dict[str, list[str]] = {
    "girl": ["Lina", "Mira", "Nella", "Tavi", "Zuri"],
    "boy": ["Ari", "Beni", "Ivo", "Milo", "Rafi"],
}

HEALER_NAMES = ["Doctor Hale", "Doctor Imani", "Doctor Sefa", "Doctor Vale"]


def pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return "he", "him", "his"
    return "she", "her", "her"


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.misreading not in MISREADINGS:
        return False, f"Unknown misreading: {params.misreading!r}."
    if params.virtue not in VIRTUES:
        return False, f"Unknown virtue: {params.virtue!r}."
    if params.tooth_case not in TOOTH_CASES:
        return False, f"Unknown tooth case: {params.tooth_case!r}."
    if params.gender not in HERO_NAMES:
        return False, f"Unknown gender: {params.gender!r}."
    misreading = MISREADINGS[params.misreading]
    virtue = VIRTUES[params.virtue]
    if virtue.key not in misreading.compatible_virtues:
        return (
            False,
            f"{misreading.title.title()} is not reasonably healed by {virtue.label} alone in this world; "
            f"choose one of {', '.join(misreading.compatible_virtues)}.",
        )
    return True, ""


def valid_combos() -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for misreading in sorted(MISREADINGS):
        for virtue in sorted(VIRTUES):
            for tooth_case in sorted(TOOTH_CASES):
                params = StoryParams(
                    misreading=misreading,
                    virtue=virtue,
                    tooth_case=tooth_case,
                    hero="Lina",
                    gender="girl",
                    healer="Doctor Hale",
                    seed=0,
                )
                ok, _ = valid_params(params)
                if ok:
                    rows.append((misreading, virtue, tooth_case))
    return rows


def build_world(params: StoryParams) -> World:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)

    misreading = MISREADINGS[params.misreading]
    virtue = VIRTUES[params.virtue]
    tooth_case = TOOTH_CASES[params.tooth_case]

    hero = Entity(
        name=params.hero,
        kind="child",
        meters={"pain": tooth_case.pain_level, "jaw_tension": 0.72, "breath_speed": 0.78},
        memes={"fear": 0.79, "trust": 0.24, "wonder": 0.36, "relief": 0.08},
        states={"ache": tooth_case.symptom, "belief": misreading.false_belief, "position": "doorway"},
    )
    healer = Entity(
        name=params.healer,
        kind="dentist",
        meters={"steadiness": 0.93, "gentle_touch": 0.88},
        memes={"kindness": 0.94, "wisdom": 0.89},
        states={"role": "guide of teeth"},
    )
    candle = Entity(
        name="beeswax candle",
        kind="object",
        meters={"glow": 0.81, "flame_height": 0.57, "wax_softness": 0.18},
        memes={"hope": 0.41, "wonder": 0.53},
        states={"shape": "a crooked fang of wax", "place": "beside the mint bowl"},
    )
    office = Entity(
        name="dentist office",
        kind="place",
        meters={"echo": 0.47, "shine": 0.76},
        memes={"calm": 0.28},
        states={"style": "mythic", "smell": "mint and clove"},
    )
    waiting_child = Entity(
        name="a younger child by the window",
        kind="child",
        meters={"fidget": 0.51},
        memes={"fear": 0.42, "wonder": 0.34},
        states={"position": "bench by the window"},
    )

    world = World(
        params=params,
        misreading=misreading,
        virtue=virtue,
        tooth_case=tooth_case,
        entities={
            "hero": hero,
            "healer": healer,
            "candle": candle,
            "office": office,
            "waiting_child": waiting_child,
        },
    )
    simulate(world)
    return world


def simulate(world: World) -> None:
    hero = world.entities["hero"]
    healer = world.entities["healer"]
    candle = world.entities["candle"]
    waiting_child = world.entities["waiting_child"]

    world.events.append("arrival")
    hero.memes["fear"] = min(1.0, hero.memes["fear"] + 0.09)
    hero.meters["jaw_tension"] = min(1.0, hero.meters["jaw_tension"] + 0.08)
    world.events.append("misreading_takes_hold")

    if world.virtue.key == "truth":
        hero.memes["trust"] += 0.33
        hero.memes["relief"] += 0.14
        hero.states["spoken_turn"] = "admitted the fear and pointed to the tooth"
    elif world.virtue.key == "courage":
        hero.memes["trust"] += 0.28
        hero.memes["wonder"] += 0.08
        hero.states["spoken_turn"] = "sat in the chair despite the trembling"
    elif world.virtue.key == "patience":
        hero.memes["trust"] += 0.25
        hero.meters["breath_speed"] = max(0.18, hero.meters["breath_speed"] - 0.27)
        hero.states["spoken_turn"] = "counted breaths until the room made sense"
    else:
        hero.memes["trust"] += 0.24
        hero.memes["relief"] += 0.11
        waiting_child.memes["fear"] = max(0.08, waiting_child.memes["fear"] - 0.17)
        hero.states["spoken_turn"] = "softened the room for the smaller child as well"
    world.events.append(f"virtue_{world.virtue.key}")

    hero.memes["fear"] = max(0.12, hero.memes["fear"] - 0.42)
    hero.states["belief"] = "the room can be understood and helped"
    hero.states["position"] = "chair"
    world.events.append("truth_revealed")

    candle.meters["wax_softness"] = min(1.0, candle.meters["wax_softness"] + 0.49)
    candle.meters["flame_height"] = min(1.0, candle.meters["flame_height"] + 0.07)
    candle.states["shape"] = world.virtue.final_glow
    world.events.append("candle_transformed")

    hero.meters["pain"] = max(0.05, hero.meters["pain"] - world.tooth_case.pain_relief)
    hero.meters["jaw_tension"] = max(0.09, hero.meters["jaw_tension"] - 0.34)
    hero.memes["trust"] = min(1.0, hero.memes["trust"] + 0.29)
    hero.memes["relief"] = min(1.0, hero.memes["relief"] + 0.52)
    healer.states["last_help"] = world.tooth_case.remedy
    world.events.append("tooth_eased")

    world.resolved = True
    world.moral = world.virtue.teaching
    world.final_image = (
        f"{world.params.hero} stepped back into the bright hall while {candle.states['shape']} "
        f"glimmered beside the mint bowl, and {world.tooth_case.ending_image}."
    )
    world.story = render_story(world)


def render_story(world: World) -> str:
    hero = world.entities["hero"]
    healer = world.entities["healer"]
    candle = world.entities["candle"]
    subject, obj, poss = pronouns(world.params.gender)

    p1 = (
        f"In the little dentist office that children called {world.office_title}, a beeswax candle burned beside the mint bowl, "
        f"and its vivid light laid gold across the tiled walls. {world.params.hero} came there with {world.tooth_case.symptom}, "
        f"yet {world.misreading.omen_phrase}. For a breath, {subject} believed that {world.misreading.false_belief}, "
        f"so {subject} {world.misreading.reaction}."
    )

    kindness_tail = ""
    if world.virtue.key == "kindness":
        kindness_tail = " A younger child on the bench stopped fidgeting when the gentle words filled the room."

    p2 = (
        f"Then {world.params.hero} chose {world.virtue.label}. \"{world.virtue.speech}\" {world.params.hero} said, and {healer.name} did not laugh. "
        f"The healer {world.misreading.helper_action}; then {world.misreading.reveal}. {world.params.hero} {world.virtue.child_action}, "
        f"and the fear in {poss} chest began to loosen.{kindness_tail}"
    )

    p3 = (
        f"After that, {healer.name} {world.tooth_case.remedy}, and the hurting place no longer ruled the morning. "
        f"{world.virtue.candle_change} {world.moral} When {world.params.hero} left the dentist office, "
        f"{candle.states['shape']} glimmered on the saucer, and {world.tooth_case.ending_image}."
    )
    return f"{p1}\n\n{p2}\n\n{p3}"


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a child-facing myth set in a dentist office.",
        f"Include a candle, vivid light, a misunderstanding about {world.misreading.tool_name}, and a turn powered by {world.virtue.label}.",
        f"Resolve both the fear and {world.tooth_case.symptom} with a visible transformation at the end.",
    ]


def story_questions(world: World) -> list[QAItem]:
    hero = world.entities["hero"]
    candle = world.entities["candle"]
    waiting_child = world.entities["waiting_child"]
    items = [
        QAItem(
            "Why was the child frightened at the start?",
            f"{world.params.hero} misread the room and thought that {world.misreading.false_belief}. That mistake made the dentist office feel dangerous before the healer had even touched the sore tooth.",
        ),
        QAItem(
            "What misunderstanding was corrected?",
            f"The healer showed that {world.misreading.reveal}. Once the sign was explained, the fear lost its false story and the room became ordinary again.",
        ),
        QAItem(
            f"How did {world.virtue.label} change the story?",
            f"{world.params.hero} {world.virtue.child_action}. Because of that choice, the healer could help with the real problem instead of wrestling with a hidden fear.",
        ),
        QAItem(
            "What happened to the candle?",
            f"The candle changed from a crooked fang of wax into {candle.states['shape']}. That visible transformation proved that the room had turned from confusion toward understanding.",
        ),
        QAItem(
            "How was the tooth problem eased?",
            f"{world.entities['healer'].name} {world.tooth_case.remedy}. After the care was done, {world.tooth_case.ending_image}.",
        ),
    ]
    if world.virtue.key == "kindness":
        items.append(
            QAItem(
                "Who else was helped by the child's choice?",
                f"{waiting_child.name.capitalize()} was helped too. When {world.params.hero} spoke gently, that smaller child did not have to borrow the same fear.",
            )
        )
    else:
        items.append(
            QAItem(
                "What moral does the story teach?",
                f"It teaches {world.virtue.label}. {world.moral}",
            )
        )
    return items


def world_questions(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why does telling a dentist where a tooth hurts matter?",
            "A healer can only mend the real trouble when the child points to it clearly. Honest detail turns worry into useful care.",
        ),
        QAItem(
            "Why can sounds and shadows scare children in a clinic?",
            "Unfamiliar rooms can make ordinary tools look larger than they are. When an adult explains the source of a sound or shadow, the room usually grows safer at once.",
        ),
        QAItem(
            "Why is a visible ending image helpful in a child myth?",
            "A visible ending lets children see that the inner change became real in the world. The new image holds the lesson in memory after the fear is gone.",
        ),
        QAItem(
            "What kind of courage does a gentle dentist world praise?",
            "It praises courage that works with truth, patience, or kindness instead of loud force. The brave act is to stay present long enough for care to happen.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.story,
        prompts=generation_prompts(world),
        story_qa=story_questions(world),
        world_qa=world_questions(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts"]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.extend(["", "== (2) Story questions"])
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.extend(["", "== (3) World-knowledge questions"])
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("")
        print(sample.world.trace())
    if qa:
        print("")
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mythic dentist-office candle transformation storyworld.")
    parser.add_argument("--misreading", choices=sorted(MISREADINGS))
    parser.add_argument("--virtue", choices=sorted(VIRTUES))
    parser.add_argument("--tooth-case", choices=sorted(TOOTH_CASES), dest="tooth_case")
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HERO_NAMES))
    parser.add_argument("--healer")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true", help="render every valid combination")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true", help="list valid combinations from the inline ASP gate")
    parser.add_argument("--verify", action="store_true", help="check ASP parity and exercise generated stories")
    parser.add_argument("--show-asp", action="store_true", help="print the ASP facts plus rules")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    combos = [
        combo for combo in valid_combos()
        if (args.misreading is None or combo[0] == args.misreading)
        and (args.virtue is None or combo[1] == args.virtue)
        and (args.tooth_case is None or combo[2] == args.tooth_case)
    ]
    if not combos:
        fallback = StoryParams(
            misreading=args.misreading or "hook_shadow",
            virtue=args.virtue or "truth",
            tooth_case=args.tooth_case or "sore_molar",
            hero=args.hero or "Lina",
            gender=args.gender or "girl",
            healer=args.healer or HEALER_NAMES[0],
            seed=(args.seed or 1000) + index,
        )
        ok, reason = valid_params(fallback)
        raise StoryError(reason if not ok else "No valid story matches the requested options.")

    misreading_key, virtue_key, tooth_case_key = rng.choice(combos)
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or rng.choice(HERO_NAMES[gender])
    healer = args.healer or rng.choice(HEALER_NAMES)
    return StoryParams(
        misreading=misreading_key,
        virtue=virtue_key,
        tooth_case=tooth_case_key,
        hero=hero,
        gender=gender,
        healer=healer,
        seed=(args.seed or 1000) + index,
    )


ASP_RULES = r"""
virtue(V) :- virtue_cfg(V).
misreading(M) :- misreading_cfg(M).
tooth_case(T) :- tooth_case_cfg(T).

safe(M,V,T) :- misreading(M), virtue(V), tooth_case(T), compatible(M,V).

#show safe/3.
"""


def asp_facts() -> str:
    import asp

    rows: list[str] = []
    for misreading in MISREADINGS.values():
        rows.append(asp.fact("misreading_cfg", misreading.key))
        for virtue in misreading.compatible_virtues:
            rows.append(asp.fact("compatible", misreading.key, virtue))
    for virtue in VIRTUES.values():
        rows.append(asp.fact("virtue_cfg", virtue.key))
    for tooth_case in TOOTH_CASES.values():
        rows.append(asp.fact("tooth_case_cfg", tooth_case.key))
    return "\n".join(rows)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}".rstrip() + "\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show safe/3."))
    return sorted(set(asp.atoms(model, "safe")))


def _story_is_strong(sample: StorySample) -> tuple[bool, str]:
    world = sample.world
    if world is None:
        return False, "world model missing"
    text = sample.story
    hero = world.entities["hero"]
    candle = world.entities["candle"]
    if "candle" not in text.lower() or "vivid" not in text.lower():
        return False, "seed language missing"
    if "dentist office" not in text.lower():
        return False, "setting language missing"
    if text.count("\n\n") < 2:
        return False, "story shape missing beginning-turn-ending"
    if not world.resolved:
        return False, "world never resolved"
    if hero.meters["pain"] >= world.tooth_case.pain_level:
        return False, "tooth pain did not improve"
    if hero.memes["fear"] >= 0.5:
        return False, "fear stayed too high"
    if candle.states["shape"] == "a crooked fang of wax":
        return False, "candle never transformed"
    if len(sample.prompts) < 3 or len(sample.story_qa) < 5 or len(sample.world_qa) < 4:
        return False, "output sets too thin"
    if any(len(qa.answer.split()) < 10 for qa in sample.story_qa):
        return False, "story QA regressed to short answers"
    if any(token in text for token in ("{", "}", "  ")):
        return False, "story leaked scaffold text"
    return True, ""


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set != asp_set:
        print("ASP/Python mismatch:")
        if python_set - asp_set:
            print("  only in Python:", sorted(python_set - asp_set))
        if asp_set - python_set:
            print("  only in ASP:", sorted(asp_set - python_set))
        return 1

    for index, combo in enumerate(sorted(python_set), start=1):
        params = StoryParams(
            misreading=combo[0],
            virtue=combo[1],
            tooth_case=combo[2],
            hero="Lina",
            gender="girl",
            healer="Doctor Hale",
            seed=10_000 + index,
        )
        sample = generate(params)
        ok, reason = _story_is_strong(sample)
        if not ok:
            raise StoryError(f"Generated story failed verification for {combo}: {reason}.")
    print(f"OK: inline ASP gate matches Python and exercised {len(python_set)} mythic dentist-office stories.")
    return 0


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed or 7
    samples: list[StorySample] = []
    for index, combo in enumerate(valid_combos(), start=1):
        params = StoryParams(
            misreading=combo[0],
            virtue=combo[1],
            tooth_case=combo[2],
            hero=args.hero or "Lina",
            gender=args.gender or "girl",
            healer=args.healer or "Doctor Hale",
            seed=base_seed + index,
        )
        samples.append(generate(params))
    return samples


def _emit_variants(samples: list[StorySample], args: argparse.Namespace) -> None:
    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = (
                f"### misreading={params.misreading} virtue={params.virtue} "
                f"tooth_case={params.tooth_case}"
            )
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


def main() -> int:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe/3."))
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print("\t".join(combo))
        return 0

    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []

    try:
        if args.all:
            samples = _sample_all(args)
        else:
            seen: set[str] = set()
            attempts = 0
            while len(samples) < args.n and attempts < max(args.n * 60, 60):
                params = resolve_params(args, random.Random(base_seed + attempts), index=attempts)
                sample = generate(params)
                attempts += 1
                if sample.story in seen:
                    continue
                seen.add(sample.story)
                samples.append(sample)
            if len(samples) < args.n:
                raise StoryError("Could not generate enough unique mythic dentist-office stories with those constraints.")

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        _emit_variants(samples, args)
        return 0
    except StoryError as err:
        print(err)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
