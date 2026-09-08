#!/usr/bin/env python3
"""
A small fable world about a medicinal herb, a quiet chapel, and the moral value
of honesty when a frightened child remembers an earlier kindness.

The simulation tracks people, places, an herb, physical meters, emotional memes,
and a flashback that changes the hero's decision.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent / "storyworlds"))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    region: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("dry", "safe", "fresh", "weak", "warm"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "greed", "trust", "courage", "gratitude", "shame", "relief"):
            self.memes.setdefault(key, 0.0)


@dataclass(frozen=True)
class FableArc:
    warning: str
    temptation: str
    danger: str
    flashback: str
    dialogue: str
    choice: str
    repair: str
    result: str
    moral: str
    ending: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child: str = "Luna"
    keeper: str = "Sister Mara"
    chapel: str = "the hill chapel"
    herb: str = "silverleaf"
    villager: str = "Grandmother Iva"
    moral_value: str = "honesty"
    flashback: bool = True


NAMES = ["Luna", "Mira", "Tomas", "Nell", "Pia", "Jon"]
KEEPERS = ["Sister Mara", "Brother Elian", "Sister Ruth", "Father Ansel"]
CHAPELS = ["the hill chapel", "the blue-door chapel", "the chapel by the bell tower"]
HERBS = ["silverleaf", "moonmint", "golden balm", "blue sage"]
VILLAGERS = ["Grandmother Iva", "Old Tomas", "Aunt Ren", "Little Pella"]

ARCS = [
    FableArc(
        warning="Use only what the sick need, and leave the rest for tomorrow",
        temptation="hide an extra bundle of medicinal silverleaf beneath her shawl",
        danger="a feverish child in the next village would have no fresh leaves for a cooling tea",
        flashback="the time Sister Mara had shared the last cup of broth with Luna during a winter storm",
        dialogue="Sister Mara asked, \"What is heavier, a secret bundle or an honest heart?\" Luna whispered, \"The secret bundle.\"",
        choice="return the hidden leaves and speak the truth",
        repair="placed the extra silverleaf back in the chapel's labeled basket",
        result="the keeper measured enough tea for both homes, and the feverish child soon rested more easily",
        moral="Honesty is a kindness because it lets everyone receive a fair share.",
        ending="At sunset, the chapel bell rang above two warm windows, and Luna carried no secret weight.",
    ),
    FableArc(
        warning="A remedy is a promise, not a prize",
        temptation="take the brightest medicinal moonmint for herself",
        danger="the old miller would lose the dose that eased his aching chest",
        flashback="the old miller once repaired Luna's broken lantern without asking for payment",
        dialogue="The miller said, \"Will you keep the brightest leaf, or keep the promise?\" Luna answered, \"The promise.\"",
        choice="give the brightest leaf to the person who needed it",
        repair="set the moonmint beside the miller's cup and told the keeper what she had done",
        result="the miller breathed more freely, and Luna learned that fairness can shine brighter than a prize",
        moral="A moral value is shown by what we give away when nobody could stop us.",
        ending="The brightest leaf rested in the miller's cup while the chapel windows caught the dawn.",
    ),
    FableArc(
        warning="Mark every medicinal jar before you carry it through the dark",
        temptation="swap two unlabeled jars so her own errand would be quicker",
        danger="a thirsty traveler might receive bitter bark instead of the gentle remedy",
        flashback="a traveler had once stopped to guide Luna home when fog hid the chapel path",
        dialogue="The keeper said, \"Who helped you find the path?\" Luna replied, \"A stranger who read the signs.\"",
        choice="slow down and read each label aloud",
        repair="matched every jar to its painted mark and asked for a second check",
        result="the traveler received the right remedy, and the chapel store remained orderly",
        moral="Careful truthfulness protects people who may never know your name.",
        ending="Under the chapel lamp, every jar stood with its label facing the door.",
    ),
    FableArc(
        warning="Do not promise a cure when you only carry a remedy",
        temptation="boast that her medicinal herb could heal every sorrow",
        danger="a worried family might delay seeking the help their mother truly needed",
        flashback="the keeper had once admitted uncertainty and still helped Luna find a wise doctor",
        dialogue="Luna asked, \"Is a small truth useful?\" The keeper said, \"More useful than a grand promise.\"",
        choice="tell the family exactly what the herb could and could not do",
        repair="explained the herb's humble purpose and sent for the village healer",
        result="the family received proper help while the herb soothed the mother's throat",
        moral="The moral value of truth is strongest when hope makes exaggeration tempting.",
        ending="The herb warmed one cup, while the healer's lantern brought the larger hope.",
    ),
]

OPENINGS = [
    "At the edge of a green village stood a little chapel with a bell like a silver acorn.",
    "Near the old chapel, where thyme grew between the stones, Luna helped care for the village remedies.",
    "Every morning the chapel door opened to sunlight, dust, and the clean scent of medicinal leaves.",
    "The chapel was small, but its remedy shelf held many hopes in jars of blue and brown glass.",
]

LESSONS = [
    "A quiet truth can carry more medicine than a loud boast.",
    "What we share in secret still shapes the whole village.",
    "A kind choice is not smaller because nobody applauds it.",
    "When fear pulls one way, a remembered kindness can point home.",
]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def make_world(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity("child", "character", "child", params.child, "chapel"))
    keeper = world.add(Entity("keeper", "character", "keeper", params.keeper, "chapel"))
    herb = world.add(Entity("herb", "thing", "medicinal_herb", params.herb, "remedy shelf"))
    chapel = world.add(Entity("chapel", "place", "chapel", params.chapel, "hill"))
    villager = world.add(Entity("villager", "character", "villager", params.villager, "village"))

    child.memes.update({"worry": 1.0, "greed": 0.0, "trust": 1.0})
    keeper.memes["trust"] = 1.0
    herb.meters.update({"fresh": 1.0, "safe": 1.0, "dry": 1.0})
    chapel.meters["safe"] = 1.0
    villager.memes["worry"] = 1.0
    world.facts.update(
        child=child,
        keeper=keeper,
        herb=herb,
        chapel=chapel,
        villager=villager,
        params=params,
    )
    return world


def tell(params: StoryParams) -> World:
    world = make_world(params)
    child: Entity = world.facts["child"]
    keeper: Entity = world.facts["keeper"]
    herb: Entity = world.facts["herb"]
    villager: Entity = world.facts["villager"]
    variant = params.seed if params.seed is not None else sum(ord(c) for c in params.child + params.herb)
    arc = ARCS[variant % len(ARCS)]
    opening = OPENINGS[(variant // len(ARCS)) % len(OPENINGS)]
    lesson = LESSONS[(variant // 3) % len(LESSONS)]

    world.say(
        f"{opening} {keeper.label} trusted {child.label} to dust the remedy shelf, "
        f"where the medicinal {herb.label} waited in a small woven basket."
    )
    world.say(
        f"That morning, {villager.label} needed the {herb.label}, and {keeper.label} warned, "
        f"\"{arc.warning}.\""
    )
    world.para()

    child.memes["greed"] += 1.0
    herb.meters["safe"] = 0.0
    world.say(
        f"But {child.label} felt a small selfish wish grow large. "
        f"The child decided to {arc.temptation}."
    )
    world.say(f"Then the trouble became clear: {arc.danger}.")
    child.memes["worry"] += 1.0
    child.memes["shame"] += 1.0
    world.say(
        f"For one trembling moment, {child.label} remembered a flashback: {arc.flashback}."
    )
    world.say(arc.dialogue)
    world.say(
        f"The memory awakened the moral value of {params.moral_value}. "
        f"{child.label} chose to {arc.choice}."
    )

    child.memes["courage"] += 1.0
    child.memes["trust"] += 1.0
    child.memes["gratitude"] += 1.0
    child.memes["relief"] += 1.0
    child.memes["greed"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["shame"] = 0.0
    herb.meters["safe"] = 1.0
    herb.meters["fresh"] = 1.0
    world.fired.add("flashback")
    world.fired.add("honesty")
    world.say(f"With careful hands, {child.label} {arc.repair}.")
    world.say(f"Because the truth was spoken in time, {arc.result}.")
    world.para()
    world.say(f"{keeper.label} smiled, not because {child.label} had been perfect, but because the repair was honest.")
    world.say(f"{child.label} learned: {arc.moral}")
    world.say(f"{lesson} {arc.ending}")

    world.facts.update(arc=arc, lesson=lesson, resolved=True)
    return world


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    child: Entity = world.facts["child"]
    keeper: Entity = world.facts["keeper"]
    herb: Entity = world.facts["herb"]
    villager: Entity = world.facts["villager"]
    arc: FableArc = world.facts["arc"]
    return [
        QAItem(
            f"Who cared for the medicinal {herb.label} in {params.chapel}?",
            f"{child.label} cared for the medicinal {herb.label} with help from {keeper.label}. The chapel shelf held it for villagers who needed a remedy.",
        ),
        QAItem(
            f"What selfish action did {child.label} consider in the chapel?",
            f"{child.label} decided to {arc.temptation}. That choice could have kept the remedy from {villager.label}, who needed it.",
        ),
        "What did the flashback remind the child about?",
        f"The flashback reminded {child.label} that {arc.flashback}. Remembering that kindness made the child reconsider the selfish plan.",
        "What moral value changed the child's decision?",
        f"The moral value was {params.moral_value}. It led {child.label} to {arc.choice}, even though hiding the mistake would have been easier.",
        f"How did the medicinal remedy reach the person who needed it?",
        f"{child.label} {arc.repair}. Because the child told the truth and repaired the mistake, {arc.result}.",
        f"What happened at the end of the fable in {params.chapel}?",
        f"{arc.ending} The ending shows that {child.label}'s honest choice changed the chapel and the village for the better.",
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a chapel?", "A chapel is a small place used for prayer, quiet reflection, or gathering."),
        QAItem("What does medicinal mean?", "Medicinal means useful for helping prevent or ease sickness."),
        QAItem("What is a moral value?", "A moral value is a principle, such as honesty or kindness, that helps guide good choices."),
        QAItem("What is a flashback?", "A flashback is a remembered event from the past shown while a story is happening in the present."),
    ]


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    arc: FableArc = world.facts["arc"]
    return [
        f"Write a fable set in {params.chapel} where {params.child} must protect medicinal {params.herb}.",
        f"Tell a fable about the moral value of {params.moral_value}, using this flashback: {arc.flashback}.",
        f"Write a child-friendly chapel story in which honesty helps {params.villager} receive a medicinal remedy.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id:8} ({entity.type:14}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
warned(child).
tempted(child).
needs_remedy(villager).
remembered_kindness(child).
tells_truth(child).
returns_herb(child).

folly(child) :- warned(child), tempted(child).
flashback(child) :- remembered_kindness(child).
moral_choice(child) :- flashback(child), tells_truth(child), returns_herb(child).
remedy_shared(villager) :- needs_remedy(villager), returns_herb(child).
resolved(child) :- moral_choice(child), remedy_shared(villager).

#show folly/1.
#show flashback/1.
#show moral_choice/1.
#show remedy_shared/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("warned", "child"),
            asp.fact("tempted", "child"),
            asp.fact("needs_remedy", "villager"),
            asp.fact("remembered_kindness", "child"),
            asp.fact("tells_truth", "child"),
            asp.fact("returns_herb", "child"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    actual = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {
        "folly/1",
        "flashback/1",
        "moral_choice/1",
        "remedy_shared/1",
        "resolved/1",
    }
    if actual != expected:
        print("MISMATCH:", sorted(actual), "expected", sorted(expected))
        return 1
    for seed in range(12):
        sample = generate(StoryParams(seed=seed))
        if not sample.story or "flashback" not in sample.story.lower():
            print("MISMATCH: generated story missing flashback")
            return 1
        if not sample.world.facts.get("resolved"):
            print("MISMATCH: generated world unresolved")
            return 1
    print("OK: ASP twin and generated chapel fables agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A medicinal chapel fable with moral value and flashback.")
    parser.add_argument("--child", choices=NAMES)
    parser.add_argument("--keeper", choices=KEEPERS)
    parser.add_argument("--chapel", choices=CHAPELS)
    parser.add_argument("--herb", choices=HERBS)
    parser.add_argument("--villager", choices=VILLAGERS)
    parser.add_argument("--moral-value", choices=["honesty", "kindness", "fairness", "care"])
    parser.add_argument("--no-flashback", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        child=args.child or rng.choice(NAMES),
        keeper=args.keeper or rng.choice(KEEPERS),
        chapel=args.chapel or rng.choice(CHAPELS),
        herb=args.herb or rng.choice(HERBS),
        villager=args.villager or rng.choice(VILLAGERS),
        moral_value=args.moral_value or rng.choice(["honesty", "kindness", "fairness", "care"]),
        flashback=not args.no_flashback,
    )


def generate(params: StoryParams) -> StorySample:
    if not params.flashback:
        raise StoryError("This fable requires a flashback so the remembered kindness can guide the moral choice.")
    if params.child == params.villager:
        raise StoryError("The child and the person needing the remedy must be different characters.")
    world = tell(params)
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


CURATED = [
    StoryParams(seed=0, child="Luna", keeper="Sister Mara", chapel="the hill chapel", herb="silverleaf", villager="Grandmother Iva", moral_value="honesty"),
    StoryParams(seed=1, child="Mira", keeper="Brother Elian", chapel="the blue-door chapel", herb="moonmint", villager="Old Tomas", moral_value="fairness"),
    StoryParams(seed=2, child="Nell", keeper="Sister Ruth", chapel="the chapel by the bell tower", herb="golden balm", villager="Aunt Ren", moral_value="care"),
    StoryParams(seed=3, child="Pia", keeper="Father Ansel", chapel="the hill chapel", herb="blue sage", villager="Little Pella", moral_value="kindness"),
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
        print(" ".join(str(symbol) for symbol in asp.one_model(asp_program())))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            seed = base_seed + index
            index += 1
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
