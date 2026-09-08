#!/usr/bin/env python3
"""
A standalone Storyweavers world: a child-friendly superhero story about bacon,
a surprising twist, and reconciliation.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "storyworlds", "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


THEME = "Sunbeam City"
SEED_WORDS = {"bacon", "remove"}


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = "city_square"

    def __post_init__(self) -> None:
        for key in ("speed", "noise", "smoke", "damage", "distance"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "courage", "trust", "anger", "joy", "regret"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    hero: str = "Luna"
    partner: str = "Milo"
    rival: str = "Vex"
    trial: int = 0
    voice: int = 0
    twist_style: int = 0
    ending_style: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trial:
    mission: str
    trouble: str
    clue: str
    false_guess: str
    twist: str
    admission: str
    repair: str
    proof: str
    lesson: str
    ending: str
    snack: str


TRIALS = [
    Trial(
        mission="protect the Lantern Parade",
        trouble="a runaway delivery cart sprayed hot bacon smoke across the square",
        clue="a trail of shiny grease drops leading toward the old clock tower",
        false_guess="the crowd first blamed Vex because his purple cape was seen near the cart",
        twist="the cart's remote control had been stuck under a paper bacon wrapper",
        admission="I grabbed breakfast while testing the remote, and the wrapper slipped beneath the button",
        repair="removed the wrapper, cooled the cart, and guided the parade behind a safe line",
        proof="the cart stopped, the smoke cleared, and every lantern reached the river",
        lesson="A quick accusation can hide the real cause; careful questions give trust room to return.",
        ending="Luna's silver star shone above the quiet cart as the lanterns floated like tiny moons.",
        snack="a bacon sandwich",
    ),
    Trial(
        mission="rescue the rooftop garden",
        trouble="the garden's water balloon machine began flinging bacon-scented bubbles at the flowers",
        clue="a red button wedged beneath a strip of crispy bacon",
        false_guess="everyone suspected Luna had pressed the emergency button with her glove",
        twist="the machine had been set to clean mode, but a hungry pigeon had dragged bacon onto the controls",
        admission="I left the snack near the machine, and the pigeon caused the trouble while I chased it",
        repair="removed the bacon, reset the machine, and watered the garden by hand",
        proof="the roses stood tall, the bubbles stopped, and the machine watered only the flower beds",
        lesson="Reconciliation begins when people explain what happened and help repair the result.",
        ending="The rooftop roses opened beneath Luna's cape while the rescued pigeon pecked crumbs far from the controls.",
        snack="a bacon biscuit",
    ),
    Trial(
        mission="keep the Moonbeam Museum safe",
        trouble="the museum's alarm began shouting whenever someone carried bacon past the front door",
        clue="a warm lunch wrapper pressed against the alarm's red sensor",
        false_guess="the guards thought Vex had designed a new noisy trick",
        twist="the sensor was not detecting bacon at all; it was reacting to heat from the wrapper",
        admission="I tucked my lunch beside the sensor while hiding from the rain, and I should have told someone",
        repair="removed the wrapper, cooled the sensor, and posted a clear lunch spot by the entrance",
        proof="visitors could enter quietly, and the alarm stayed ready for real danger",
        lesson="A mistake does not have to become a permanent enemy story.",
        ending="The museum doors opened in peace, and Luna and Vex watched moon rocks sparkle inside.",
        snack="a bacon roll",
    ),
    Trial(
        mission="deliver the city's hero badges",
        trouble="the badge balloon rose away with a basket full of bacon-shaped medals",
        clue="a loose red ribbon caught on a rooftop weather vane",
        false_guess="Milo guessed that Vex had cut the basket loose to steal attention",
        twist="the ribbon had snagged the vane, and a gust pulled the basket free",
        admission="I tied the ribbon too quickly because I was hungry and wanted to finish my bacon first",
        repair="removed the ribbon from the vane, lowered the basket, and retied every badge with a double knot",
        proof="the second balloon stayed steady while all the heroes received their medals",
        lesson="Owning a small careless choice can make a large repair possible.",
        ending="The final badge gleamed on Luna's chest as the balloon bobbed safely above the square.",
        snack="a bacon-and-cheese bun",
    ),
    Trial(
        mission="save the school science fair",
        trouble="a robot vacuum began chasing the bacon display and bumping the science tables",
        clue="a bacon crumb glowing beneath the robot's front sensor",
        false_guess="the students thought Vex had programmed the robot to cause a commotion",
        twist="the robot was following the crumb's heat, not anyone's command",
        admission="I dropped the bacon while setting up, then pretended not to notice because I was embarrassed",
        repair="removed the crumb, stopped the robot, and helped rebuild the tipped experiment",
        proof="the robot cleaned in straight lines and the rebuilt volcano erupted safely",
        lesson="Honesty can turn embarrassment into a chance to be useful.",
        ending="The science fair buzzed again, and Luna awarded the repaired robot a careful-helper sticker.",
        snack="a bacon muffin",
    ),
]


@dataclass
class World:
    hero: Entity
    partner: Entity
    rival: Entity
    bacon: Entity
    beacon: Entity
    cart: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def entity(eid: str, kind: str, type_: str, label: str, location: str = "city_square") -> Entity:
    return Entity(id=eid, kind=kind, type=type_, label=label, location=location)


def build_world(params: StoryParams) -> World:
    world = World(
        hero=entity(params.hero, "character", "hero", "the young superhero"),
        partner=entity(params.partner, "character", "helper", "the superhero's partner"),
        rival=entity(params.rival, "character", "rival", "the misunderstood rival"),
        bacon=entity("bacon", "food", "snack", "a piece of bacon"),
        beacon=entity("beacon", "machine", "signal", "the moonbeam beacon"),
        cart=entity("cart", "vehicle", "delivery_cart", "the delivery cart"),
    )
    world.facts["theme"] = THEME
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    h, p, r = world.hero, world.partner, world.rival
    trial = TRIALS[params.trial % len(TRIALS)]

    h.memes["courage"] = 2
    p.memes["trust"] = 1
    r.memes["worry"] = 1
    r.memes["anger"] = 1
    world.bacon.meters["smoke"] = 1
    world.cart.meters["noise"] = 2
    world.cart.meters["damage"] = 1

    openings = [
        f"In {THEME}, Luna wore a bright cape and watched over the streets as the city prepared to {trial.mission}.",
        f"The sun rose over {THEME}, where {h.id} and {p.id} practiced heroic rescues before setting out to {trial.mission}.",
        f"At the heart of {THEME}, the moonbeam beacon blinked above a busy day. {h.id} had one important mission: {trial.mission}.",
        f"{h.id} promised to help every neighbor in {THEME}. Today, the promise mattered because the heroes had to {trial.mission}.",
    ]
    world.say(openings[params.voice % len(openings)])
    world.say(f"Then {trial.trouble}.")
    world.say(f"The bacon smell curled through the air, and the beacon flashed a worried blue.")

    world.para()
    world.say(f"{trial.clue}.")
    world.say(f"At first, {trial.false_guess}.")
    h.memes["worry"] += 1
    r.memes["anger"] += 1

    thoughts = [
        f"{h.id} lifted a hand. 'A cape is not proof. We need to follow the clue: {trial.clue}.'",
        f"{h.id} studied the ground. 'Before we blame anyone, we should ask what the {trial.clue} can tell us.'",
        f"{h.id} said, 'Heroes protect people from unfair guesses too. Let us test the evidence.'",
        f"{h.id} touched the beacon and whispered, 'The safest rescue starts with knowing what really happened.'",
    ]
    world.say(thoughts[params.twist_style % len(thoughts)])
    dialogue = [
        f"'{h.id}, do you still trust me?' {r.id} asked. 'I trust the truth to help us decide,' {h.id} replied.",
        f"'{p.id}, should we remove the bacon first?' {h.id} asked. 'Yes,' said {p.id}. 'Then we can see what the machine is doing.'",
        f"'{r.id}, did you cause this?' {p.id} asked. 'I do not know,' {r.id} said. 'That is why I want to look.'",
        f"'No shouting,' {h.id} told the crowd. 'Questions can be brave, too.' {r.id} nodded and stepped closer.",
    ]
    world.say(dialogue[(params.voice + params.twist_style) % len(dialogue)])
    world.say("Together, they followed the physical clue instead of the easy accusation.")

    world.para()
    world.say(f"The first search led to the machine, where {trial.twist}.")
    r.memes["worry"] += 1
    r.memes["anger"] = max(0, r.memes["anger"] - 1)
    world.say(f"{h.id} found the missing connection and said, 'The problem is not the person we guessed about. It is the thing caught in the wrong place.'")
    world.say(f"{r.id} took a slow breath. 'I can explain. {trial.admission}.'")
    r.memes["regret"] += 1
    h.memes["trust"] += 1
    world.say(f"{h.id} answered, 'Thank you for telling us. Now we can repair it together.'")

    world.para()
    world.say(f"The heroes {trial.repair}.")
    world.say(f"{trial.proof}.")
    h.memes["joy"] += 2
    p.memes["trust"] += 1
    r.memes["trust"] += 2
    r.memes["anger"] = 0
    world.say(f"{p.id} offered {r.id} the last safe bite of {trial.snack}. {r.id} smiled and shared it instead of hiding.")

    world.para()
    world.say(f"The crowd learned that {trial.lesson}")
    endings = [
        trial.ending,
        f"After the cheers faded, {trial.ending}",
        f"{h.id} lowered the beacon's blue shield, and {trial.ending}",
        f"Even {r.id} joined the final salute. {trial.ending}",
    ]
    world.say(endings[params.ending_style % len(endings)])

    world.facts.update(
        hero=h,
        partner=p,
        rival=r,
        trial=trial,
        mission=trial.mission,
        trouble=trial.trouble,
        clue=trial.clue,
        false_guess=trial.false_guess,
        twist=trial.twist,
        admission=trial.admission,
        repair=trial.repair,
        proof=trial.proof,
        lesson=trial.lesson,
        ending=trial.ending,
        snack=trial.snack,
        reconciliation=True,
        resolved=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    h = world.facts["hero"]
    p = world.facts["partner"]
    r = world.facts["rival"]
    return [
        QAItem(
            question=f"What trouble interrupted {h.id}'s mission?",
            answer=f"The mission was interrupted because {world.facts['trouble']}.",
        ),
        QAItem(
            question="What clue helped the heroes understand the problem?",
            answer=f"They followed {world.facts['clue']} instead of relying on the first accusation.",
        ),
        QAItem(
            question="What was the surprising twist?",
            answer=f"The twist was that {world.facts['twist']}.",
        ),
        QAItem(
            question=f"How did {r.id} help with reconciliation?",
            answer=f"{r.id} admitted, '{world.facts['admission']}.' Then the heroes worked together to {world.facts['repair']}.",
        ),
        QAItem(
            question=f"How did {h.id}, {p.id}, and {r.id} know the problem was fixed?",
            answer=f"They knew because {world.facts['proof']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a character who uses special abilities, courage, or helpful skills to protect people and solve problems.",
        ),
        QAItem(
            question="What does remove mean?",
            answer="Remove means to take something away from a place so that it is no longer there.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is the process of repairing trust after a disagreement or mistake by telling the truth, listening, and making things better.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change in what the reader thought was happening.",
        ),
        QAItem(
            question="Why should people check evidence before blaming someone?",
            answer="Checking evidence helps people find the real cause and prevents an unfair accusation from hurting someone.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a child-friendly superhero story in {THEME} where bacon causes trouble during the mission to {world.facts['mission']}.",
        f"Include the twist that {world.facts['twist']}.",
        f"Show reconciliation after {world.facts['rival'].id} explains, '{world.facts['admission']}.', and let the heroes repair the problem together.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
    lines = ["--- world model state ---"]
    for item in (
        world.hero,
        world.partner,
        world.rival,
        world.bacon,
        world.beacon,
        world.cart,
    ):
        meters = {k: v for k, v in item.meters.items() if v}
        memes = {k: v for k, v in item.memes.items() if v}
        lines.append(
            f"  {item.id:10} ({item.kind:9}) location={item.location} "
            f"meters={meters} memes={memes}"
        )
    lines.append(f"  resolved={world.facts.get('resolved')}")
    lines.append(f"  reconciliation={world.facts.get('reconciliation')}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(sunbeam_city).
requires(sunbeam_city, bacon).
requires(sunbeam_city, remove).
feature(sunbeam_city, twist).
feature(sunbeam_city, reconciliation).
style(sunbeam_city, superhero_story).

valid_story(S) :-
    setting(S),
    requires(S, bacon),
    requires(S, remove),
    feature(S, twist),
    feature(S, reconciliation),
    style(S, superhero_story).

resolved_story(S) :- valid_story(S).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("setting", "sunbeam_city"),
            asp.fact("requires", "sunbeam_city", "bacon"),
            asp.fact("requires", "sunbeam_city", "remove"),
            asp.fact("feature", "sunbeam_city", "twist"),
            asp.fact("feature", "sunbeam_city", "reconciliation"),
            asp.fact("style", "sunbeam_city", "superhero_story"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(
        asp_program("#show valid_story/1.\n#show resolved_story/1.")
    )
    names = {atom.name for atom in model}
    if "valid_story" in names and "resolved_story" in names:
        print("OK: ASP and Python recognize the bacon superhero domain.")
        return 0
    print("MISMATCH: ASP did not recognize the required story features.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero stories about bacon, twists, and reconciliation."
    )
    parser.add_argument("--hero", default=None)
    parser.add_argument("--partner", default=None)
    parser.add_argument("--rival", default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: int,
    base_seed: int,
) -> StoryParams:
    hero = args.hero or rng.choice(["Luna", "Nova", "Skye", "Ari", "Zara"])
    partner = args.partner or rng.choice(["Milo", "Pip", "Theo", "Remy", "Nia"])
    rival = args.rival or rng.choice(["Vex", "Glim", "Rook", "Shade"])
    if len({hero, partner, rival}) != 3:
        raise StoryError("The hero, partner, and rival must have different names.")
    offset = sample_seed - base_seed
    return StoryParams(
        hero=hero,
        partner=partner,
        rival=rival,
        trial=offset % len(TRIALS),
        voice=(offset // len(TRIALS)) % 4,
        twist_style=(offset // (len(TRIALS) * 4)) % 4,
        ending_style=(offset // (len(TRIALS) * 4 * 4)) % 4,
        seed=sample_seed,
    )


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


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(hero="Luna", partner="Milo", rival="Vex", trial=0),
    StoryParams(hero="Nova", partner="Pip", rival="Glim", trial=1),
    StoryParams(hero="Skye", partner="Theo", rival="Rook", trial=2),
    StoryParams(hero="Ari", partner="Remy", rival="Shade", trial=3),
    StoryParams(hero="Zara", partner="Nia", rival="Vex", trial=4),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1.\n#show resolved_story/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(
            asp_program("#show valid_story/1.\n#show resolved_story/1.")
        )
        print("ASP model:", [str(atom) for atom in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 50)
        while len(samples) < args.n and index < limit:
            sample_seed = base_seed + index
            params = resolve_params(
                args,
                random.Random(sample_seed),
                sample_seed,
                base_seed,
            )
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = (
            f"### variant {index + 1}"
            if len(samples) > 1 and not args.all
            else ""
        )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
