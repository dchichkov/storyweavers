#!/usr/bin/env python3
"""
storyworlds/worlds/frame_share_email_bad_ending_curiosity_superhero.py
======================================================================

A small superhero storyworld about curiosity, a suspicious email, sharing, and
a bad ending.

Seed premise:
- A young superhero notices a strange email.
- Curiosity pushes the hero to open it and share it.
- The message is a trap that frames a friend.
- The ending is bad: trust is damaged, and the villain escapes.

The world model tracks both physical state (meters) and emotional state (memes)
so the prose can follow the simulation instead of acting like a static template.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    target: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    indoors: bool = True
    has_console: bool = False
    has_window: bool = False


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    kind: str
    risky: bool = False


@dataclass
class StoryParams:
    place: str
    hero: str
    sidekick: str
    villain: str
    artifact: str
    email_subject: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


PLACES = {
    "tower": Place("the tower", indoors=True, has_console=True, has_window=True),
    "hideout": Place("the hideout", indoors=True, has_console=True, has_window=False),
    "rooftop": Place("the rooftop room", indoors=False, has_console=False, has_window=True),
}

HEROES = ["Nova", "Spark", "Comet", "Luna", "Dash", "Mira"]
SIDEKICKS = ["Pip", "Jet", "Kit", "Bree", "Tess"]
VILLAINS = ["Doctor Shade", "Captain Glare", "Mister Rust", "The Moth", "Venom Vex"]
SUBJECTS = [
    "urgent news",
    "a secret map",
    "a hero badge",
    "a missing key",
    "a rescue plan",
]

ARTIFACTS = {
    "frame": Artifact(
        id="frame",
        label="frame",
        phrase="a silver frame on the wall",
        kind="frame",
        risky=True,
    ),
    "email": Artifact(
        id="email",
        label="email",
        phrase="a strange email on the screen",
        kind="email",
        risky=True,
    ),
    "share": Artifact(
        id="share",
        label="share button",
        phrase="a bright share button",
        kind="share",
        risky=True,
    ),
}

CURATED = [
    StoryParams(place="tower", hero="Nova", sidekick="Pip", villain="Doctor Shade", artifact="email", email_subject="a secret map"),
    StoryParams(place="hideout", hero="Spark", sidekick="Kit", villain="Captain Glare", artifact="share", email_subject="urgent news"),
    StoryParams(place="rooftop", hero="Luna", sidekick="Bree", villain="The Moth", artifact="frame", email_subject="a missing key"),
]


def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.hero, kind="character", type="girl" if params.hero in {"Nova", "Luna", "Mira"} else "boy", traits=["brave", "curious"]))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="boy" if params.sidekick in {"Pip", "Jet", "Kit"} else "girl", traits=["helpful"]))
    villain = world.add(Entity(id=params.villain, kind="character", type="man", traits=["sly"]))
    artifact = ARTIFACTS[params.artifact]
    inbox = world.add(Entity(id="inbox", kind="thing", type="screen", label="screen", phrase="the glowing screen"))
    message = world.add(Entity(id="message", kind="thing", type="email", label="email", phrase=f'an email about "{params.email_subject}"', owner=villain.id, target=hero.id))
    frame = world.add(Entity(id="frame", kind="thing", type="frame", label="frame", phrase="a shiny frame", owner=hero.id))

    world.facts.update(hero=hero, sidekick=sidekick, villain=villain, artifact=artifact, message=message, frame=frame, inbox=inbox, params=params)
    return world


def _curiosity(world: World) -> None:
    hero: Entity = world.facts["hero"]
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(f"{hero.id} noticed a strange email blinking on the screen and leaned closer.")
    world.say(f"{hero.pronoun().capitalize()} could not stop wondering who had sent it.")


def _open_email(world: World) -> None:
    hero: Entity = world.facts["hero"]
    villain: Entity = world.facts["villain"]
    message: Entity = world.facts["message"]
    hero.meters["seen_email"] = hero.meters.get("seen_email", 0.0) + 1
    world.say(f"{hero.id} opened the email. It looked harmless at first, but it was really a trap from {villain.id}.")
    world.say(f"The message tried to frame {world.facts['sidekick'].id} for a stolen hero badge.")
    world.fired.add(("opened", message.id))


def _share(world: World) -> None:
    hero: Entity = world.facts["hero"]
    sidekick: Entity = world.facts["sidekick"]
    hero.meters["shared"] = hero.meters.get("shared", 0.0) + 1
    hero.memes["trust_risk"] = hero.memes.get("trust_risk", 0.0) + 1
    world.say(f"{hero.id} shared the email before thinking it through, hoping the team would help.")
    world.say(f"But the share button spread the trap faster, and even {sidekick.id} looked worried.")
    world.fired.add(("shared", hero.id))


def _frame_damage(world: World) -> None:
    sidekick: Entity = world.facts["sidekick"]
    villain: Entity = world.facts["villain"]
    sidekick.memes["blamed"] = sidekick.memes.get("blamed", 0.0) + 1
    sidekick.memes["hurt"] = sidekick.memes.get("hurt", 0.0) + 1
    world.say(f"By the time the team understood the trick, {sidekick.id} had already been framed.")
    world.say(f"{villain.id} slipped away in the confusion, and the heroes were left with a broken trust.")


def tell_story(world: World) -> None:
    hero: Entity = world.facts["hero"]
    sidekick: Entity = world.facts["sidekick"]
    villain: Entity = world.facts["villain"]
    artifact: Artifact = world.facts["artifact"]

    world.say(f"In {world.place.name}, {hero.id} and {sidekick.id} wore their capes and watched the quiet room.")
    world.say(f"On the wall was {artifact.phrase}, and on the desk was a mysterious email that did not belong there.")

    world.para()
    _curiosity(world)
    world.say(f"{hero.id} should have called for help, but curiosity pulled harder than caution.")
    _open_email(world)
    _share(world)
    _frame_damage(world)

    world.para()
    world.say(f"At the end, the heroes stared at the screen in silence.")
    world.say(f"The email had fooled them, {sidekick.id} was blamed unfairly, and the villain was gone.")
    world.say(f"{hero.id} learned that in a superhero story, curiosity can be dangerous when it is shared too fast.")

    world.facts["ending_bad"] = True
    world.facts["curiosity"] = True
    world.facts["shared"] = True
    world.facts["framed"] = True


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a short superhero story with the words frame, share, and email.",
        f"Tell a kid-friendly superhero tale where {p.hero} sees an email, feels curiosity, and decides whether to share it.",
        f"Create a story in which a villain uses an email to frame a friend, and the ending is bad.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    hero: Entity = world.facts["hero"]
    sidekick: Entity = world.facts["sidekick"]
    villain: Entity = world.facts["villain"]
    return [
        QAItem(
            question=f"Why did {hero.id} open the email?",
            answer=f"{hero.id} opened the email because curiosity made the message seem important and exciting.",
        ),
        QAItem(
            question=f"What happened when {hero.id} shared the email?",
            answer=f"Sharing the email spread the trap faster, which made the trouble worse instead of better.",
        ),
        QAItem(
            question=f"Who got framed in the story?",
            answer=f"{sidekick.id} got framed by the villain's trick inside the email.",
        ),
        QAItem(
            question=f"Why is the ending bad?",
            answer=f"The ending is bad because the villain escaped and {sidekick.id} was blamed unfairly, so the heroes lost trust and the problem was not fixed.",
        ),
        QAItem(
            question=f"Where did the story happen?",
            answer=f"It happened at {world.place.name}, where the heroes were watching the screen and the suspicious email appeared.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an email?",
            answer="An email is a message sent through a computer or phone so people can read it quickly.",
        ),
        QAItem(
            question="What does it mean to share something?",
            answer="To share something means to let other people see it or use it too.",
        ),
        QAItem(
            question="What does frame mean in a story like this?",
            answer="To frame someone means to make them look guilty even when they did not do anything wrong.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to know more about something new or strange.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.kind}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
curious(hero) :- curiosity(hero).
shared(hero) :- shared(hero).
framed(sidekick) :- framed(sidekick).
bad_ending :- curious(hero), shared(hero), framed(sidekick).

#show curious/1.
#show shared/1.
#show framed/1.
#show bad_ending/0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("curiosity", "hero"))
    lines.append(asp.fact("shared", "hero"))
    lines.append(asp.fact("framed", "sidekick"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/0."))
    atoms = asp.atoms(model, "bad_ending")
    if atoms == [()]:
        print("OK: ASP reasoner agrees the story ends badly.")
        return 0
    print("Mismatch: ASP reasoner did not find the bad ending.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with frame, share, email, curiosity, and a bad ending.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--villain", choices=VILLAINS)
    ap.add_argument("--artifact", choices=ARTIFACTS.keys())
    ap.add_argument("--email-subject", choices=SUBJECTS)
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
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(HEROES)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    villain = args.villain or rng.choice(VILLAINS)
    artifact = args.artifact or rng.choice(list(ARTIFACTS))
    email_subject = args.email_subject or rng.choice(SUBJECTS)
    if hero == sidekick:
        raise StoryError("The hero and sidekick must be different characters.")
    if hero == villain or sidekick == villain:
        raise StoryError("The villain must be different from the heroes.")
    return StoryParams(place=place, hero=hero, sidekick=sidekick, villain=villain, artifact=artifact, email_subject=email_subject)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
        print(asp_program("#show bad_ending/0."))
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
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} at {p.place} with {p.artifact}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
