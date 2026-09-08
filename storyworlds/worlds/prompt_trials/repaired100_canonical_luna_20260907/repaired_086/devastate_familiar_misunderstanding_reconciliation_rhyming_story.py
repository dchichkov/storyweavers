#!/usr/bin/env python3
"""Rhyming StoryWorld about a familiar mistake, devastation, and reconciliation."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
sys.path.insert(0, os.path.dirname(_storyworlds_dir))
from results import QAItem, StoryError, StorySample  # noqa: E402


FRIEND_NAMES = ["Luna", "Milo", "Nia", "Tess", "Pip", "Arlo", "Suri", "Bea"]
PLACES = ["the moonlit garden", "the familiar orchard", "the bluebell yard"]
HELPERS = ["the patient badger", "the gentle robin", "the wise tortoise"]

@dataclass(frozen=True)
class CASE:
    id: str
    object_name: str
    familiar_sign: str
    misunderstanding: str
    harm: str
    clue: str
    cause: str
    repair: str
    image: str
    rhyme: str

CASES = (
    CASE("nest", "a woven bird nest", "a familiar red ribbon tied to a branch",
         "the robin had ruined the nest to steal Luna's ribbon",
         "the robin flew away sadly and left the nest unfinished",
         "soft blue feathers were tucked beneath the broken twigs",
         "a gust had carried the ribbon into the nest while the robin was away",
         "reweaving the nest with safe grass and freeing the ribbon",
         "the robin resting in a strong nest beneath the moon",
         "Tie with care, repair and share"),
    CASE("lantern", "a little garden lantern", "a familiar muddy footprint beside its glass",
         "the badger had smashed the lantern while sneaking through the flowers",
         "the path became dark and the badger felt accused",
         "tiny paw prints stopped before the lantern, while wheel tracks crossed behind it",
         "a wheelbarrow bumped the lantern during a storm cleanup",
         "replacing the glass and marking a safer garden path",
         "warm lantern light guiding every friend home",
         "Glow, know, ask before you go"),
    CASE("cake", "a berry cake", "a familiar purple smear on the empty plate",
         "Milo had eaten the cake and pretended not to know",
         "the birthday table fell quiet and Milo hid behind a bush",
         "purple berries were crushed beneath the open window",
         "rainwater had washed the cake from the cooling sill",
         "baking a new cake and sharing the berries fairly",
         "friends smiling around a fresh cake with purple stars",
         "Taste, trace, mend the mistake"),
    CASE("map", "the orchard map", "a familiar curl in the missing corner",
         "the tortoise had torn the map to keep everyone from the best apples",
         "the apple hunt stopped and trust began to wilt",
         "the torn corner matched a bramble snag by the gate",
         "the wind had dragged the map through the brambles",
         "smoothing, copying, and posting the map beneath a stone",
         "friends following the restored map through golden trees",
         "Read, heed, let friendship lead"),
    CASE("drum", "a small festival drum", "a familiar green thread on its loose strap",
         "Nia had broken the drum to stop the rehearsal",
         "the festival rhythm vanished and Nia was blamed",
         "the thread also clung to a thorn beside the storage shed",
         "the strap caught on the thorn when a fox carried the drum",
         "mending the strap and moving the drum to a safer shelf",
         "a bright drumbeat welcoming everyone to dance",
         "Tap, clap, bring music back"),
)

OPENINGS = (
    "At dawn, when silver dew made every spiderweb shine",
    "One bright morning, beneath a sky of blueberry blue",
    "As evening painted the garden gold",
    "Before breakfast, while the small birds sang",
    "When moonlight pooled along the quiet path",
)
BRIDGES = (
    "Luna paused, then asked a question instead of making a claim.",
    "The friends compared the places, marks, and times they knew.",
    "A careful look turned a loud guess into a quiet clue.",
    "They listened to every voice before choosing what to do.",
    "The familiar sign mattered, but it did not tell the whole story.",
)
APOLOGIES = (
    '"I misunderstood," Luna said. "I am sorry. Let us repair this together."',
    '"I blamed you too soon," said Luna. "Your truth deserved a careful question."',
    '"My guess caused hurt," Luna admitted. "I will help make things right."',
    '"A familiar mark is not proof," Luna said. "Please forgive my mistake."',
)

@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

@dataclass
class StoryParams:
    place: str
    friend_name: str
    helper: str
    case_id: str = "nest"
    opening_id: int = 0
    bridge_id: int = 0
    apology_id: int = 0
    seed: Optional[int] = None

@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        return copy.deepcopy(self)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rhyming StoryWorld about misunderstanding and reconciliation.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--friend-name", choices=FRIEND_NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument(f"--{flag}", action="store_true", dest=flag.replace("-", "_"))
    return parser

def get_case(case_id: str) -> CASE:
    for case in CASES:
        if case.id == case_id:
            return case
    raise StoryError(f"Unknown case: {case_id}")

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "familiar_garden"),
        asp.fact("feature", "misunderstanding"),
        asp.fact("feature", "reconciliation"),
        asp.fact("style", "rhyming_story"),
        asp.fact("theme", "devastate"),
        asp.fact("safety", "ask_before_blame"),
    ])

ASP_RULES = """
valid_story :-
    setting(familiar_garden),
    feature(misunderstanding),
    feature(reconciliation),
    style(rhyming_story),
    theme(devastate),
    safety(ask_before_blame).
#show valid_story/0.
"""

def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    ok = any(symbol.name == "valid_story" for symbol in model)
    print("OK: ASP gate accepted the misunderstanding and reconciliation story." if ok
          else "Mismatch: ASP gate rejected the story.")
    return 0 if ok else 1

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        friend_name=args.friend_name or rng.choice(FRIEND_NAMES),
        helper=args.helper or rng.choice(HELPERS),
        case_id=rng.choice(CASES).id,
        opening_id=rng.randrange(len(OPENINGS)),
        bridge_id=rng.randrange(len(BRIDGES)),
        apology_id=rng.randrange(len(APOLOGIES)),
    )

def tell(params: StoryParams) -> World:
    case = get_case(params.case_id)
    w = World(params.place)
    friend = w.add(Entity("friend", "character", "child", params.friend_name, "questioner"))
    helper = w.add(Entity("helper", "animal", "helper", params.helper, "witness"))
    w.add(Entity("object", "thing", "familiar_object", case.object_name, "shared treasure"))
    w.facts.update(case=case, friend=friend, helper=helper, resolved=False,
                   emotional_harm=0.0, practical_harm=1.0)

    w.say(f"{OPENINGS[params.opening_id]}, {friend.label} visited {params.place}.")
    w.say(f"{helper.label.capitalize()} waved from beside {case.object_name}, a treasure familiar to them both.")
    w.say(f"They had cared for it together, and it made the garden feel safe and bright.")
    w.para()
    w.say(f"Then {friend.label} saw {case.familiar_sign}, and the sight seemed plain.")
    w.say(f"{friend.label} misunderstood and decided that {case.misunderstanding}.")
    w.say(f'"You did this!" {friend.label} cried. "{case.harm}."')
    w.say(f'{helper.label.capitalize()} answered, "Please ask me. A familiar sign can still have another cause."')
    friend.memes.update(anger=1.0, certainty=1.0)
    helper.memes.update(hurt=1.0)
    w.para()
    w.say(BRIDGES[params.bridge_id])
    w.say(f'{friend.label} asked, "What did you see, and where did it begin?"')
    w.say(f'{helper.label.capitalize()} replied, "I saw that {case.clue}."')
    w.say(f"Together they discovered the truth: {case.cause}.")
    w.say(f"The misunderstanding had felt ready to devastate their friendship, but evidence opened a kinder path.")
    w.para()
    w.say(APOLOGIES[params.apology_id])
    w.say(f"{friend.label} and {helper.label} worked side by side, {case.repair}.")
    w.say(f"The practical harm was repaired, and the hurt in their voices grew soft.")
    w.say(f'"Ask, check, care, repair!" they chanted. "{case.rhyme}!"')
    w.say(f"They learned that a familiar clue is a beginning for questions, not a reason for blame.")
    w.say(f"By nightfall, {case.image}.")
    friend.memes.update(anger=0.0, humility=1.0, trust=1.0)
    helper.memes.update(hurt=0.0, trust=1.0)
    w.facts.update(resolved=True, emotional_harm=0.0, practical_harm=0.0,
                   clue=case.clue, cause=case.cause, repair=case.repair, image=case.image)
    return w

def generation_prompts(w: World) -> list[str]:
    case = w.facts["case"]
    name = w.facts["friend"].label
    return [
        f"Write a rhyming story in which {name} misunderstands {case.familiar_sign}.",
        f"Show how a misunderstanding could devastate trust, then lead to reconciliation.",
        f"End with {case.image}, using the words devastate and familiar naturally.",
    ]

def story_qa(w: World) -> list[QAItem]:
    case = w.facts["case"]
    name = w.facts["friend"].label
    helper = w.facts["helper"].label
    return [
        QAItem(
            f"Why did {name} misunderstand the situation?",
            f"{name} saw {case.familiar_sign} and assumed that {case.misunderstanding}. The familiar sign looked convincing, but it was not proof."
        ),
        QAItem(
            "What clue revealed the truth?",
            f"The clue was that {case.clue}. It showed that {case.cause}."
        ),
        QAItem(
            f"How did {helper} respond to the accusation?",
            f"{helper.capitalize()} asked {name} to listen and explain what had been seen. That conversation replaced a quick blame with evidence."
        ),
        QAItem(
            "How was the harm repaired?",
            f"They apologized and worked together by {case.repair}. The object was restored and their trust returned."
        ),
        QAItem(
            "What proves reconciliation happened?",
            f"The story ends with {case.image}. Their shared work and peaceful ending prove that reconciliation followed the misunderstanding."
        ),
    ]

def world_knowledge_qa(w: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a misunderstanding?",
            "A misunderstanding happens when someone gives the wrong meaning to words, signs, or events. Asking a careful question can uncover the truth."
        ),
        QAItem(
            "What does reconciliation mean?",
            "Reconciliation means repairing a relationship after conflict. It usually needs listening, responsibility, apology, and helpful action."
        ),
        QAItem(
            "Why can a familiar clue be misleading?",
            "A familiar clue may resemble something known without proving its cause. Good friends check the place, timing, and other evidence before blaming someone."
        ),
        QAItem(
            "What does devastate mean?",
            "Devastate means to damage something very badly or cause deep sadness. In this story, an unfair accusation could devastate trust, but honesty and repair prevent that result."
        ),
    ]

def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.type} {entity.label} role={entity.role} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    for key in ("clue", "cause", "repair", "emotional_harm", "practical_harm", "resolved"):
        lines.append(f"  fact.{key}={world.facts.get(key)}")
    return "\n".join(lines)

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))

CURATED = [
    StoryParams("the moonlit garden", "Luna", "the patient badger", "nest", 0, 0, 0),
    StoryParams("the familiar orchard", "Milo", "the wise tortoise", "map", 1, 2, 1),
    StoryParams("the bluebell yard", "Nia", "the gentle robin", "drum", 3, 4, 2),
]

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        print("compatible story:")
        for symbol in asp.one_model(asp_program()):
            print(symbol)
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(100, args.n * 30):
            seed = base + attempt
            attempt += 1
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
