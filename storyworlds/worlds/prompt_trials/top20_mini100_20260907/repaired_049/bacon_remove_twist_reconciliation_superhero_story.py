#!/usr/bin/env python3
"""
A small superhero storyworld about a bacon problem, a removal, a twist, and a
reconciliation.

The seed premise:
- A superhero city has a tiny lunch hall problem involving bacon.
- A small mistake means someone needs to remove the bacon from the wrong tray.
- The story turns on a Twist: the real problem is not the bacon itself, but a
  misunderstanding about who it was for.
- Reconciliation follows when the hero listens, repairs the mix-up, and helps
  everyone share the meal.

The story is state-driven:
- meters track carried items, noise, and repair progress
- memes track pride, annoyance, worry, and trust
- spoken dialogue changes what characters know and do
- the ending proves the fix through changed world state
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

STORYWORLDS_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)
sys.path.insert(0, STORYWORLDS_ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def them(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "Hero Harbor Community Hall"
    affords: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Scenario:
    id: str
    opening: str
    problem: str
    first_guess: str
    twist: str
    dialogue: str
    shared_action: str
    reconciliation: str
    ending: str
    lesson: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def meme(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def add_meter(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = meter(e, key) + amt


def add_meme(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = meme(e, key) + amt


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        hero = world.entities.get("Nova")
        chef = world.entities.get("Chef Lina")
        teammate = world.entities.get("Bram")
        if hero and meme(hero, "worry") >= THRESHOLD and meme(hero, "curiosity") >= THRESHOLD:
            sig = ("focus", hero.id)
            if sig not in world.fired:
                world.fired.add(sig)
                add_meme(hero, "focus", 1.0)
                out.append(f"{hero.id} slowed down and looked closely instead of guessing.")
                changed = True
        if hero and meter(hero, "returned") >= THRESHOLD and meme(hero, "trust") < THRESHOLD:
            sig = ("trust", hero.id)
            if sig not in world.fired:
                world.fired.add(sig)
                add_meme(hero, "trust", 1.0)
                out.append(f"The others trusted {hero.id} more after the careful return.")
                changed = True
        if chef and meter(chef, "repaired") >= THRESHOLD and meme(chef, "annoyance") < THRESHOLD:
            sig = ("relief", chef.id)
            if sig not in world.fired:
                world.fired.add(sig)
                add_meme(chef, "relief", 1.0)
                out.append(f"{chef.id} felt relieved that the lunch hall was whole again.")
                changed = True
        if teammate and meter(teammate, "shared") >= THRESHOLD and meme(teammate, "trust") < THRESHOLD:
            sig = ("trust2", teammate.id)
            if sig not in world.fired:
                world.fired.add(sig)
                add_meme(teammate, "trust", 1.0)
                out.append(f"{teammate.id} saw that sharing was safer than arguing.")
                changed = True
    if narrate:
        for line in out:
            world.say(line)
    return out


SETTING = Setting(
    place="Hero Harbor Community Hall",
    affords={"sharing", "listening", "repair"},
)

SCENARIOS = [
    Scenario(
        "tray_mixup",
        "At noon, the lunch hall filled with the smell of toast, soup, and one heroic plate of bacon.",
        "A tray had been set in the wrong place, and the bacon was about to go to the wrong table.",
        "Nova first tried to remove the bacon fast, before asking whose lunch it was.",
        "The twist was simple: the bacon belonged to the tiny rescue crew, not to the noisy line by the door.",
        "Nova, can we check the note before you remove it?",
        "carry the tray back to the kitchen and read the name tag aloud",
        "The mix-up ended in reconciliation when everyone laughed, apologized, and split the meal fairly.",
        "The rescue crew got their bacon, the hall got calmer, and nobody was left hungry.",
        "Sometimes a wrong tray is really a wrong guess.",
    ),
    Scenario(
        "label_scarf",
        "A red scarf on the service cart meant the spicy soup, but today it had slipped over the bacon plate instead.",
        "The hall-keeper worried the plate would vanish before the little heroes arrived.",
        "Nova nearly removed the bacon and sent it to the fridge without checking the scarf.",
        "The twist was that the scarf marked the table for the training squad, who had saved the day at dawn.",
        "Did the scarf fall by accident, or did the wind help it?",
        "tie the scarf back on the cart and walk the bacon plate to the training squad together",
        "Reconciliation came when the keeper and Nova apologized to the squad and brought extra bread as peace.",
        "The training squad smiled, the bacon stayed warm, and the scarf was pinned properly.",
        "A label can slip, but friendship can be tied back on.",
    ),
    Scenario(
        "smoke_alarm",
        "A squeaky alarm chirped near the grill, and everyone looked at the bacon sizzling on the counter.",
        "The sound made the volunteers step back, and the plate sat alone beside the heater.",
        "Nova first thought the safest move was to remove the bacon at once.",
        "The twist was that the alarm was only warning about a dusty vent, not the food.",
        "Wait—do you smell smoke, or just the grill?",
        "open the vent, fan the smoke away, and return the bacon to the serving line",
        "Reconciliation followed when Nova admitted the hurry and the volunteers forgave the scare.",
        "The alarm stopped, the vent cleared, and the bacon reached the waiting plates.",
        "A brave heart still needs a careful nose.",
    ),
    Scenario(
        "team_banner",
        "The rooftop team returned from patrol, hungry and sun-tired, just as bacon sandwiches were being plated.",
        "One sandwich had fallen under the banner table, where it could not be seen.",
        "Nova wanted to remove the bacon from the tray and replace it with something else.",
        "The twist was that the missing sandwich was a reward for the rooftop team who had guarded the city bells.",
        "Who earned the last sandwich, and what did the clipboard say?",
        "pick up the fallen sandwich, dust it off, and serve it with the other rewards",
        "Reconciliation came when the rooftop team thanked Nova for listening instead of tossing the meal away.",
        "The banner shadow lifted, and the last sandwich was eaten with bright smiles.",
        "A reward is safest when the hero checks the list first.",
    ),
    Scenario(
        "pepper_shake",
        "The cook had shaken pepper over the bacon, but the shaker lid was loose and pepper dotted the whole counter.",
        "People blamed the bacon for making the tray look messy.",
        "Nova nearly removed the bacon because it seemed blamed by everyone.",
        "The twist was that the pepper came from the shaker, not from the bacon, and the plate was still good.",
        "Can we taste one corner before we throw out the whole tray?",
        "wipe the counter, move the pepper shaker, and serve the bacon with clean napkins",
        "Reconciliation arrived when the cook and Nova agreed that the tray was worth saving.",
        "The hallkeeper set out napkins, and the bacon plate returned to the table shining.",
        "Not every mess means the meal is ruined.",
    ),
]


DIALOGUES = [
    "Can we check the note before you remove it?",
    "Who was this plate meant for?",
    "Did the tray move, or did our guess move?",
    "Can I look one more time before we decide?",
    "What does the label say in small letters?",
    "Is the bacon the problem, or is the table the problem?",
]


@dataclass
class StoryParams:
    place: str
    scenario: str
    hero: str
    sidekick: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld about bacon, removal, twist, and reconciliation.")
    ap.add_argument("--place", choices=["hero_harbor"], default="hero_harbor")
    ap.add_argument("--scenario", choices=[s.id for s in SCENARIOS])
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
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
    scenario = args.scenario or rng.choice([s.id for s in SCENARIOS])
    hero = args.hero or rng.choice(["Nova", "Captain Crisp", "Spark"])
    sidekick = args.sidekick or rng.choice(["Bram", "Iris", "Milo"])
    return StoryParams(place="hero_harbor", scenario=scenario, hero=hero, sidekick=sidekick)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place != "hero_harbor":
        raise StoryError("This storyworld only supports Hero Harbor.")
    if params.scenario not in {s.id for s in SCENARIOS}:
        raise StoryError("Unknown superhero scenario.")
    if not params.hero or not params.sidekick:
        raise StoryError("Both a hero and a sidekick are needed for the reconciliation story.")


def tell(world: World, params: StoryParams) -> World:
    scenario = next(s for s in SCENARIOS if s.id == params.scenario)
    variant = params.seed if params.seed is not None else sum((i + 1) * ord(ch) for i, ch in enumerate(f"{params.hero}|{params.sidekick}|{scenario.id}"))
    dialogue = DIALOGUES[variant % len(DIALOGUES)]

    hero = world.add(Entity(id=params.hero, kind="character", type="person", label="hero"))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="person", label="sidekick"))
    chef = world.add(Entity(id="Chef Lina", kind="character", type="person", label="chef"))
    team = world.add(Entity(id="Team", kind="character", type="group", label="rescue crew", plural=True))
    bacon = world.add(Entity(id="Bacon Plate", kind="thing", type="plate", label="bacon", owner="Kitchen"))
    tray = world.add(Entity(id="Tray", kind="thing", type="tray", label="service tray", owner="Kitchen"))

    add_meme(hero, "curiosity", 1.0)
    add_meme(hero, "worry", 1.0)
    add_meme(chef, "annoyance", 1.0)

    openers = [
        f"In Hero Harbor, the lunch hall was part of the city's daily hero work, just like patrols and map checks.",
        f"The city had capes, alarms, and a lunch hall where even superheroes ate carefully between rescues.",
        f"Every noon in Hero Harbor, the community hall filled with bright voices and the smell of warm food.",
        f"The superheroes did not only save bridges and buses; they also kept the lunch line fair.",
    ]
    world.say(openers[variant % len(openers)])
    world.say(f"{params.hero} arrived with {params.sidekick} just as {scenario.opening.lower()}")
    world.say(scenario.problem)
    world.para()

    world.say(f"Seeing the crowded counter, {params.hero} first thought, \"I should {scenario.first_guess.split(' ', 1)[1]}\"")
    add_meter(hero, "bacon_seen", 1.0)
    add_meme(hero, "worry", 1.0)
    world.say(f"{params.sidekick} warned, \"{dialogue}\"")
    world.say(f"That question slowed the rush, and {params.hero} looked closer.")
    world.say(f"Then came the twist: {scenario.twist}")
    add_meme(hero, "curiosity", 1.0)
    add_meme(chef, "trust", 1.0)
    world.para()

    world.say(f"{params.hero} said, \"Oh! I almost made it worse.\"")
    world.say(f"{chef.id} answered, \"Thank you for not removing it without checking.\"")
    world.say(f"Together they chose to {scenario.shared_action}.")
    add_meter(hero, "returned", 1.0)
    add_meter(chef, "repaired", 1.0)
    add_meter(sidekick, "shared", 1.0)
    add_meme(hero, "trust", 1.0)
    add_meme(sidekick, "trust", 1.0)
    propagate(world)

    world.say(scenario.reconciliation)
    world.say(f"{params.sidekick} grinned and said, \"Teamwork tastes better than a guess.\"")
    world.say(f"{params.hero} laughed, and the hall answered with smiles instead of complaints.")
    world.para()

    world.say(f"By the end, {scenario.ending}")
    world.say(f"The lesson was clear: {scenario.lesson}")
    world.say("The bacon stayed where it belonged, the people calmed down, and the hero's careful listening saved the meal.")
    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        chef=chef,
        team=team,
        bacon=bacon,
        tray=tray,
        scenario=scenario,
        dialogue=dialogue,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story for children about bacon, removal, a Twist, and Reconciliation in {world.setting.place}.",
        f"Tell a complete, state-driven story where {f['hero'].id} almost removes the bacon from the wrong tray, then learns the truth.",
        f"Write a short heroic tale that includes spoken dialogue, a twist, and a happy reconciliation over a bacon lunch.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    s = f["scenario"]
    return [
        QAItem(
            question="What food caused the mix-up?",
            answer="The mix-up was about bacon on a tray in the Hero Harbor community hall.",
        ),
        QAItem(
            question="What did the hero first plan to do?",
            answer=f"{f['hero'].id} first planned to remove the bacon quickly without checking carefully.",
        ),
        QAItem(
            question="What was the twist?",
            answer=s.twist,
        ),
        QAItem(
            question="What did the sidekick say that changed the hero's mind?",
            answer=f"{f['sidekick'].id} asked: '{f['dialogue']}' That question made the hero look again.",
        ),
        QAItem(
            question="How did the characters reconcile?",
            answer=f"They reconciled by fixing the tray, apologizing, and sharing the meal fairly.",
        ),
        QAItem(
            question="What changed by the ending?",
            answer="The bacon stayed with the right group, the hall became calm, and the team trusted one another more.",
        ),
        QAItem(
            question="Why was listening important?",
            answer="Listening was important because it revealed the label error before the hero made the situation worse.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a new fact that changes what the characters thought was true.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people make up after a disagreement and start working together again.",
        ),
        QAItem(
            question="Why do superheroes help ordinary places too?",
            answer="Superheroes help ordinary places because small problems can matter just as much as big dangers.",
        ),
        QAItem(
            question="Why is bacon easy to mix up in a busy kitchen?",
            answer="Bacon can be mixed up if trays and labels are moved around in a busy kitchen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for qa in sample.story_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for qa in sample.world_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(hero_harbor).
scenario(tray_mixup;label_scarf;smoke_alarm;team_banner;pepper_shake).

valid(hero_harbor, tray_mixup).
valid(hero_harbor, label_scarf).
valid(hero_harbor, smoke_alarm).
valid(hero_harbor, team_banner).
valid(hero_harbor, pepper_shake).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "hero_harbor"),
            asp.fact("feature", "Twist"),
            asp.fact("feature", "Reconciliation"),
            asp.fact("seed_word", "bacon"),
            asp.fact("seed_word", "remove"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str]]:
    return [("hero_harbor", s.id) for s in SCENARIOS]


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    return 0 if py == cl else 1


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World(SETTING)
    world = tell(world, params)
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
    StoryParams("hero_harbor", "tray_mixup", "Nova", "Bram"),
    StoryParams("hero_harbor", "label_scarf", "Captain Crisp", "Iris"),
]


def build_sample(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp or args.asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} / {p.scenario}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
