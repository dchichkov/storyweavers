#!/usr/bin/env python3
"""
A compact whodunit-style storyworld about trust, a mimic, and an orangutan.

Premise:
A small group of friends in a rainforest research camp notices that a lantern,
a key, or a snack has gone missing. The clues point in two directions at once:
an orangutan who can move quietly through the trees, and a mimic who copies
sounds and gestures. The hero must decide whom to trust, follow the clues, and
discover the true culprit.

The domain stays small and classical:
- one setting,
- one suspicious event,
- one reveal,
- one clear ending image proving what changed.

The story engine builds the tale from world state, not from a frozen paragraph.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    trusted_by: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str
    cover: str


@dataclass
class SuspectProfile:
    id: str
    type: str
    label: str
    phrase: str
    clue_style: str
    can_mimic: bool = False
    can_hide: bool = False


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    location: str
    prized_reason: str


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    suspect: str
    prize: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "canopy_camp": Setting(
        place="the canopy camp",
        detail="Lantern light shook under the leaves while the wet boards creaked softly.",
        cover="The trees made a green roof over the camp.",
    ),
    "river_station": Setting(
        place="the river station",
        detail="The water kept whispering past the dock, and the dock ropes tapped in the dark.",
        cover="A long roof covered the supply table beside the river.",
    ),
    "night_gallery": Setting(
        place="the night gallery",
        detail="Tall display cases stood in a dim hall, each one throwing back a thin silver gleam.",
        cover="The hall was quiet enough that every tiny sound felt important.",
    ),
}

PRIZES = {
    "map": Prize(
        id="map",
        label="map",
        phrase="the camp map with the marked trail",
        location="on the supply table",
        prized_reason="it showed the safest path through the trees",
    ),
    "key": Prize(
        id="key",
        label="key",
        phrase="the little brass key",
        location="by the lantern",
        prized_reason="it opened the locked equipment box",
    ),
    "lantern": Prize(
        id="lantern",
        label="lantern",
        phrase="the bright lantern",
        location="hanging from a hook",
        prized_reason="it kept the dark corners from feeling frightening",
    ),
}

SUSPECTS = {
    "orangutan": SuspectProfile(
        id="orangutan",
        type="orangutan",
        label="orangutan",
        phrase="a quiet orangutan with long, careful arms",
        clue_style="leaf marks and a soft rustle in the branches",
        can_mimic=False,
        can_hide=True,
    ),
    "mimic": SuspectProfile(
        id="mimic",
        type="creature",
        label="mimic",
        phrase="a sneaky mimic that copies sounds and shapes",
        clue_style="borrowed voices and repeated foot taps",
        can_mimic=True,
        can_hide=True,
    ),
    "raccoon": SuspectProfile(
        id="raccoon",
        type="raccoon",
        label="raccoon",
        phrase="a clever raccoon with sticky little paws",
        clue_style="tiny muddy prints and a torn snack wrapper",
        can_mimic=False,
        can_hide=True,
    ),
}

HERO_NAMES = ["Mina", "Theo", "Lina", "Owen", "Ari", "Nora", "Eli", "Jade"]
HELPER_NAMES = ["Pip", "Sana", "Milo", "June", "Noah", "Ivy", "Remy", "Tara"]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def setting_intro(setting: Setting) -> str:
    return f"{setting.cover} {setting.detail}"


def suspicion_line(prize: Prize, suspect: SuspectProfile) -> str:
    return (
        f"Then {prize.label} went missing, and the first clue was {suspect.clue_style}."
    )


def hero_feels(hero: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1


def helper_trust(helper: Entity) -> None:
    helper.memes["trust"] = helper.memes.get("trust", 0) + 1


def suspect_state(suspect: Entity, clue: str) -> None:
    suspect.meters["suspicion"] = suspect.meters.get("suspicion", 0) + 1
    suspect.meters["clue"] = suspect.meters.get("clue", 0) + 1
    suspect.memes["unease"] = suspect.memes.get("unease", 0) + 1
    suspect.memes["narrative_clue"] = suspect.memes.get("narrative_clue", 0) + 1
    suspect.memes[clue] = suspect.memes.get(clue, 0) + 1


def reveal_truth(world: World) -> str:
    suspect = world.get("suspect")
    prize = world.get("prize")
    hero = world.get("hero")
    helper = world.get("helper")
    if suspect.type == "orangutan":
        return (
            f"The orangutan had not taken {prize.label} at all. "
            f"It had only carried it to the dry branch above the table after hearing the box creak open. "
            f"The real trickster was the mimic, which copied the orangutan's shape in the shadows "
            f"and left the camp guessing."
        )
    if suspect.type == "mimic":
        return (
            f"The mimic had borrowed the wrong sound and sent the camp chasing the wrong trail. "
            f"The orangutan had simply watched from the branches, quiet and harmless, while {prize.label} "
            f"was hidden by the mimic near the vines."
        )
    return (
        f"The raccoon had stolen {prize.label}, and the orangutan was only the strange shadow the watchers noticed first. "
        f"The mimic copied a branch scrape and made the camp doubt what it saw."
    )


def ending_image(world: World) -> str:
    hero = world.get("hero")
    helper = world.get("helper")
    prize = world.get("prize")
    suspect = world.get("suspect")
    if suspect.type == "orangutan":
        return (
            f"At last {hero.id} gave the orangutan a banana and thanked it for leading them back to {prize.label}, "
            f"while {helper.id} closed the box and smiled at the clever little rescue."
        )
    return (
        f"At last {hero.id} put {prize.label} back in its place, and {helper.id} laughed softly because the clues made sense now."
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A suspect is suspicious if the prize goes missing while the suspect is nearby.
suspicious(S) :- suspect(S), missing(prize), nearby(S).

% An orangutan can look suspicious because of branches and quiet movement.
suspicious(orangutan) :- clue(branches), clue(rustle).

% A mimic is especially suspect when sounds are copied.
suspicious(mimic) :- clue(copy_sound), clue(shadow_shape).

% The true culprit is the one that fits the missing-prize clue pattern.
culprit(S) :- suspicious(S), fit(S).

% The story resolves when the hero trusts the better clue trail.
resolved :- culprit(S), trusted(S), not false_trail(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    for pid in PRIZES:
        lines.append(asp.fact("prize_kind", pid))
    for sid, sp in SUSPECTS.items():
        if sp.can_mimic:
            lines.append(asp.fact("can_mimic", sid))
        if sp.can_hide:
            lines.append(asp.fact("can_hide", sid))
    for key in ("missing", "nearby", "fit", "trusted", "false_trail"):
        pass
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_check() -> bool:
    import asp
    model = asp.one_model(asp_program("#show suspicious/1. #show culprit/1. #show resolved/0."))
    syms = {(a[0] if len(a) == 1 else tuple(a)) for a in asp.atoms(model, "culprit")}
    return bool(syms)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    suspect_profile = SUSPECTS[params.suspect]
    suspect = world.add(Entity(id="suspect", kind="character", type=suspect_profile.type, label=suspect_profile.label))
    prize = world.add(Entity(id="prize", kind="thing", type=params.prize, label=PRIZES[params.prize].label))

    world.facts.update(
        hero=hero,
        helper=helper,
        suspect=suspect,
        prize=prize,
        suspect_profile=suspect_profile,
        prize_profile=PRIZES[params.prize],
        setting=setting,
    )

    # Act 1: setup
    world.say(f"{hero.label} came to {setting.place} with {helper.label} and trusted the quiet routine of the night.")
    world.say(setting_intro(setting))
    world.say(f"They had come to check on {prize.phrase}, because {PRIZES[params.prize].prized_reason}.")

    # Act 2: the disappearance
    world.para()
    hero_feels(hero)
    helper_trust(helper)
    world.say(
        f"Then {prize.label} was gone. {hero.label} felt a cold twist of worry, because the table still showed the empty spot where it should have been."
    )
    world.say(suspicion_line(PRIZES[params.prize], suspect_profile))
    world.say(
        f"A shadow moved near the cover, and the team noticed {suspect_profile.phrase} in the dim light."
    )
    suspect_state(suspect, suspect_profile.clue_style)

    # Act 3: the clue trail
    world.para()
    if suspect_profile.type == "orangutan":
        world.say(
            f"{helper.label} said, 'Don't blame the first face you see.' That was important, because the orangutan's long arms could reach the high branches, but the missing item was not up there yet."
        )
        world.say(
            f"Instead, {hero.label} looked for what had been copied. A soft echo of footsteps pointed away from the branches and toward the vines."
        )
        world.facts["false_trail"] = "orangutan"
        world.facts["fit"] = "mimic"
        world.facts["trusted"] = "helper"
    elif suspect_profile.type == "mimic":
        world.say(
            f"{helper.label} noticed the strange repeats: one tap, then another tap, like a sound trying to wear somebody else's face."
        )
        world.say(
            f"That made {hero.label} trust the clue instead of the fear. The orangutan in the branches had only watched, while the mimic had hidden the prize."
        )
        world.facts["false_trail"] = "orangutan"
        world.facts["fit"] = "mimic"
        world.facts["trusted"] = "helper"
    else:
        world.say(
            f"{helper.label} found muddy prints under the table, but the branches above still mattered, because something had copied a scrape in the dark."
        )
        world.facts["false_trail"] = "orangutan"
        world.facts["fit"] = "raccoon"
        world.facts["trusted"] = "helper"

    # Resolution
    world.para()
    world.say(reveal_truth(world))
    world.say(
        f"In the end, the real answer was not to fear the loudest clue. It was to trust the careful one."
    )
    world.say(ending_image(world))

    return world


def generation_prompts(world: World) -> list[str]:
    prize = world.facts["prize_profile"]
    suspect = world.facts["suspect_profile"]
    hero = world.facts["hero"]
    return [
        f"Write a suspenseful whodunit for a young child about {hero.label}, a missing {prize.label}, and a strange {suspect.label}.",
        f"Tell a short mystery story where someone must trust the right clue, even though an orangutan and a mimic both seem suspicious.",
        f"Create a gentle detective story set at {world.setting.place} with a hidden {prize.label}, a misleading shadow, and a calm solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    helper = world.get("helper")
    suspect = world.get("suspect")
    prize = world.get("prize")
    questions = [
        QAItem(
            question=f"Who tried to solve the mystery at {world.setting.place}?",
            answer=f"{hero.label} tried to solve the mystery with help from {helper.label}.",
        ),
        QAItem(
            question=f"What went missing in the story?",
            answer=f"{prize.label} went missing, and that made everyone look for clues.",
        ),
        QAItem(
            question=f"Why did the characters feel worried?",
            answer=f"They felt worried because the prize disappeared and the first clues pointed to the wrong place.",
        ),
        QAItem(
            question=f"Why did the orangutan seem important?",
            answer=f"The orangutan seemed important because it moved near the cover and its quiet movement looked suspicious in the dark.",
        ),
        QAItem(
            question=f"What helped the hero avoid blaming the wrong one?",
            answer=f"{helper.label} helped by pointing out the careful clue trail, so {hero.label} trusted the evidence instead of the first scary guess.",
        ),
        QAItem(
            question=f"What did the story prove at the end?",
            answer=f"It proved that the careful clue was right, and that trust helped solve the mystery.",
        ),
    ]
    if suspect.type == "orangutan":
        questions.append(
            QAItem(
                question="Was the orangutan the true thief?",
                answer="No. The orangutan only looked suspicious at first; the mimic was the one that misled everyone.",
            )
        )
    else:
        questions.append(
            QAItem(
                question="Was the suspicious creature really harmless?",
                answer="No, not completely. The first clue was misleading, so the team had to keep looking until the true answer appeared.",
            )
        )
    return questions


def world_knowledge_qa(world: World) -> list[QAItem]:
    suspect = world.facts["suspect_profile"]
    prize = world.facts["prize_profile"]
    out = [
        QAItem(
            question="What is an orangutan?",
            answer="An orangutan is a large ape with long arms that can climb trees and move carefully through branches.",
        ),
        QAItem(
            question="What does mimic mean?",
            answer="To mimic means to copy what someone else does or says.",
        ),
        QAItem(
            question="What is trust?",
            answer="Trust is believing that someone is being honest or helpful.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the tense feeling that makes you wonder what will happen next.",
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where readers try to figure out who caused the trouble.",
        ),
    ]
    if suspect.can_mimic:
        out.append(
            QAItem(
                question="Why can a mimic be confusing?",
                answer="A mimic can be confusing because it copies sounds or shapes, so it may seem like someone else is nearby.",
            )
        )
    if prize.id == "key":
        out.append(
            QAItem(
                question="What is a key for?",
                answer="A key is used to open a lock.",
            )
        )
    if prize.id == "lantern":
        out.append(
            QAItem(
                question="What does a lantern do?",
                answer="A lantern gives light in dark places.",
            )
        )
    if prize.id == "map":
        out.append(
            QAItem(
                question="What does a map do?",
                answer="A map shows where places are and helps you find your way.",
            )
        )
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {e.label} {' '.join(bits)}")
    lines.append(f"  facts={list(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Validity / parameter resolution
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for pr in PRIZES:
            for su in SUSPECTS:
                combos.append((s, pr, su))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld: trust, orangutan, mimic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    prize = args.prize or rng.choice(list(PRIZES))
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    if hero_name == helper_name:
        helper_name = rng.choice([n for n in HELPER_NAMES if n != hero_name])
    return StoryParams(
        setting=setting,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        suspect=suspect,
        prize=prize,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show suspicious/1. #show culprit/1. #show resolved/0."))
        return

    if args.verify:
        try:
            import asp  # lazy
        except Exception as exc:  # pragma: no cover
            raise SystemExit(f"ASP unavailable: {exc}")
        print("ASP twin is present.")
        return

    if args.asp:
        print("This world is primarily prose-first; ASP twin is embedded for parity and rule inspection.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = valid_combos()
        for s, pr, su in combos:
            params = StoryParams(
                setting=s,
                hero_name="Mina",
                hero_type="girl",
                helper_name="Pip",
                helper_type="boy",
                suspect=su,
                prize=pr,
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
