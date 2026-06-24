#!/usr/bin/env python3
"""
A standalone storyworld: a space-race marathon with sound effects and
celebratory hallelujahs.

Seed premise:
- In a small space-adventure setting, a child-sized crew prepares for a marathon
  across a moon track.
- One runner loves dramatic sound effects; the other starts worried the loud
  noises will scare the tiny robot guide.
- The turn is that the sound effects are not a problem; they become the rhythm
  that helps everyone keep pace.
- The resolution is a joyful finish with hallelujahs echoing under the stars.

This script follows the Storyworld Contract:
- self-contained stdlib script
- imports results eagerly
- lazy-imports asp helpers only in ASP functions
- defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def item_word(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    style: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    prep: str = ""
    tail: str = ""


@dataclass
class StoryParams:
    place: str
    event: str
    prize: str
    hero: str
    hero_kind: str
    ally_kind: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "moon_track": Place("moon_track", "the moon track", "space adventure", {"marathon"}),
    "star_harbor": Place("star_harbor", "Star Harbor", "space adventure", {"marathon"}),
    "orbit_dome": Place("orbit_dome", "the orbit dome", "space adventure", {"marathon", "sound_checks"}),
}

EVENTS = {
    "marathon": Event(
        id="marathon",
        verb="run the marathon",
        gerund="running the marathon",
        rush="dash down the glowing track",
        sound="tap-tap",
        keyword="marathon",
        tags={"run", "race", "space"},
    ),
    "sound_checks": Event(
        id="sound_checks",
        verb="test the sound effects",
        gerund="making sound effects",
        rush="shout into the echo tube",
        sound="pew-pew",
        keyword="sound effects",
        tags={"sound", "space"},
    ),
}

PRIZES = {
    "medal": Entity("medal", type="thing", label="medal", phrase="a shining silver medal", plural=False),
    "banner": Entity("banner", type="thing", label="banner", phrase="a bright finish banner", plural=False),
    "lucky_shoes": Entity("lucky_shoes", type="shoes", label="shoes", phrase="lucky star shoes", plural=True),
    "cape": Entity("cape", type="thing", label="cape", phrase="a comet-blue cape", plural=False),
}

GENDERS = {"girl", "boy"}
HERO_NAMES = {
    "girl": ["Nova", "Mina", "Luna", "Aria", "Zoe"],
    "boy": ["Rex", "Toby", "Milo", "Finn", "Owen"],
}
TRAITS = ["brave", "curious", "cheerful", "lively", "stubborn"]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.sound_on: bool = False
        self.finish_bell: bool = False

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

    def copy(self) -> "World":
        import copy
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.sound_on = self.sound_on
        c.finish_bell = self.finish_bell
        return c


def _act_sound(world: World, actor: Entity, event: Event, narrate: bool = True) -> list[str]:
    out = []
    sig = ("sound", actor.id, event.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    world.sound_on = True
    out.append(f"{event.sound}! {actor.id} kept the rhythm.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def _act_finish(world: World, hero: Entity, ally: Entity) -> list[str]:
    sig = ("finish", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    ally.memes["joy"] = ally.memes.get("joy", 0.0) + 1
    world.finish_bell = True
    return ["Hallelujahs rose under the stars."]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    if world.sound_on and not world.finish_bell:
        produced += _act_finish(world, world.entities["hero"], world.entities["ally"])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combo(place: Place, event: Event, prize: Entity) -> bool:
    return "marathon" in event.id and prize.label in {"medal", "banner", "shoes", "cape"} and place.id in {"moon_track", "star_harbor", "orbit_dome"}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, p in PLACES.items():
        for eid, e in EVENTS.items():
            for rid, r in PRIZES.items():
                if valid_combo(p, e, r):
                    out.append((pid, eid, rid))
    return out


def explain_rejection(place: Place, event: Event, prize: Entity) -> str:
    return f"(No story: this space setting needs a marathon prize that fits the race, and {prize.label} does not make that setup work.)"


def introduce(world: World, hero: Entity, ally: Entity, event: Event, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a big love for {event.keyword}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to {event.verb} at {world.place.label}, "
        f"and {ally.id} brought {prize.phrase} for the finish."
    )


def tension(world: World, hero: Entity, ally: Entity, event: Event, prize: Entity) -> None:
    world.para()
    world.say(
        f"At first, {ally.id} frowned at the loud {event.keyword} sounds."
    )
    world.say(
        f'"Those {event.sound} noises might spook the little rover," {ally.id} said.'
    )
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    hero.memes["wish"] = hero.memes.get("wish", 0.0) + 1
    world.say(
        f"{hero.id} held {hero.pronoun('possessive')} breath and looked at the shining {prize.label}."
    )


def turn(world: World, hero: Entity, ally: Entity, event: Event, prize: Entity) -> None:
    world.para()
    world.say(
        f"Then {hero.id} tapped {hero.pronoun('possessive')} shoes and listened to the beat: "
        f"tap-tap, {event.sound}, tap-tap."
    )
    world.say(
        f"The sound effects were not too loud after all; they were the race rhythm."
    )
    _act_sound(world, hero, event)
    propagate(world, narrate=True)


def resolve(world: World, hero: Entity, ally: Entity, event: Event, prize: Entity) -> None:
    world.para()
    world.say(
        f"{ally.id} smiled, lifted the {prize.label}, and counted the steps with the echoes."
    )
    world.say(
        f"Together they crossed the finish line, and the hallelujahs sounded like bright rockets in the dark."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    ally.memes["joy"] = ally.memes.get("joy", 0.0) + 1


def tell(place: Place, event: Event, prize: Entity, hero_name: str, hero_kind: str, ally_kind: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity("hero", kind="character", type=hero_kind, label=hero_name, plural=False))
    ally = world.add(Entity("ally", kind="character", type=ally_kind, label="the guide", plural=False))
    prize_ent = world.add(Entity("prize", type=prize.type, label=prize.label, phrase=prize.phrase, plural=prize.plural))
    world.facts.update(hero=hero, ally=ally, prize=prize_ent, event=event, place=place, trait=trait)
    introduce(world, hero, ally, event, prize_ent)
    tension(world, hero, ally, event, prize_ent)
    turn(world, hero, ally, event, prize_ent)
    resolve(world, hero, ally, event, prize_ent)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story about a child who loves "{f["event"].keyword}" and a marathon finish.',
        f"Tell a gentle story where {f['hero'].label} and the guide solve a noisy race with sound effects and end in hallelujahs.",
        f'Write a child-friendly marathon story on {world.place.label} that includes "sound effects" and a joyful ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, ally, prize, event = f["hero"], f["ally"], f["prize"], f["event"]
    return [
        QAItem(
            question=f"What did {hero.label} want to do at {world.place.label}?",
            answer=f"{hero.label} wanted to {event.verb} at {world.place.label}.",
        ),
        QAItem(
            question=f"Why did {ally.label} worry at first?",
            answer=f"{ally.label} worried because the loud {event.sound} sound effects might scare the little rover.",
        ),
        QAItem(
            question=f"What changed the mood during the story?",
            answer="The sound effects became a steady rhythm, so the worry turned into confidence.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer="They crossed the finish line together, and the hallelujahs rose under the stars.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a marathon?",
            answer="A marathon is a very long race, and runners keep going step by step until they reach the finish.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special noises made to match a scene, like taps, beeps, or whooshes.",
        ),
        QAItem(
            question="What does hallelujah mean?",
            answer="Hallelujah is a joyful word people say or sing when they feel glad and thankful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("\n== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}\nA: {qa.answer}")
    out.append("\n== (3) World knowledge ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}\nA: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type:7}) memes={dict(e.memes)} meters={dict(e.meters)}")
    lines.append(f"  sound_on={world.sound_on} finish_bell={world.finish_bell}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    event = args.event or "marathon"
    prize = args.prize or rng.choice(list(PRIZES))
    if event != "marathon":
        raise StoryError("This tiny world only supports the marathon-style space race.")
    if prize not in {"medal", "banner", "lucky_shoes", "cape"}:
        raise StoryError("That prize does not fit this storyworld.")
    hero_kind = args.hero_kind or rng.choice(sorted(GENDERS))
    if args.hero and args.hero_kind and args.hero_kind not in GENDERS:
        raise StoryError("Unknown hero kind.")
    hero = args.hero or rng.choice(HERO_NAMES[hero_kind])
    ally_kind = args.ally_kind or ("pilot" if hero_kind == "girl" else "captain")
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, event=event, prize=prize, hero=hero, hero_kind=hero_kind, ally_kind=ally_kind, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], EVENTS[params.event], PRIZES[params.prize], params.hero, params.hero_kind, params.ally_kind, params.trait)
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
hero_story(H) :- hero(H).
marathon_story(P,E,R) :- place(P), event(E), prize(R), marathon(E), compatible(P,E,R).
compatible(P,E,R) :- place(P), event(E), prize(R), marathon(E).
sound_turn(E) :- event(E), sound_event(E).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for eid, e in EVENTS.items():
        lines.append(asp.fact("event", eid))
        if eid == "marathon":
            lines.append(asp.fact("marathon", eid))
        if eid == "sound_checks":
            lines.append(asp.fact("sound_event", eid))
    for rid in PRIZES:
        lines.append(asp.fact("prize", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    clingo_set = set(asp.atoms(model, "compatible"))
    python_set = set((p, e, r) for p, e, r in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:", clingo_set ^ python_set)
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure marathon storyworld with sound effects and hallelujahs.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-kind", choices=sorted(GENDERS))
    ap.add_argument("--ally-kind")
    ap.add_argument("--trait", choices=TRAITS)
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


CURATED = [
    StoryParams("moon_track", "marathon", "medal", "Nova", "girl", "pilot", "brave"),
    StoryParams("star_harbor", "marathon", "banner", "Rex", "boy", "captain", "curious"),
    StoryParams("orbit_dome", "marathon", "lucky_shoes", "Mina", "girl", "pilot", "cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print(" ", t)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        while len(samples) < args.n and len(seen) < max(args.n * 20, 20):
            params = resolve_params(args, rng)
            params.seed = rng.randrange(2**31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
