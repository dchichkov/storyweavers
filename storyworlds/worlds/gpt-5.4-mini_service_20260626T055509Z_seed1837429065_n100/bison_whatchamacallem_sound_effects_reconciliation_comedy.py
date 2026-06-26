#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100/bison_whatchamacallem_sound_effects_reconciliation_comedy.py
===============================================================================================================

A small comedy storyworld about a bison, a whatchamacallem, silly sound
effects, and a reconciliation after a noisy misunderstanding.

The world is intentionally tiny:
- one bison with a big voice and a soft heart,
- one whatchamacallem that makes strange little noises,
- a setting where a performance or playtime can happen,
- a misunderstanding caused by sound effects,
- and a reconciliation that turns grumbles into laughter.

The prose is driven by state changes in meters and memes. The ASP twin checks
the same compatibility rule used by Python: only noisy setups that have a
plausible reconciliation are valid story seeds.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"noise": 0.0, "mess": 0.0, "care": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "grump": 0.0, "shame": 0.0, "warmth": 0.0, "conflict": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "bison":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Venue:
    place: str
    indoors: bool
    allows: set[str] = field(default_factory=set)
    acoustics: str = "echoey"


@dataclass
class Noisemaker:
    id: str
    label: str
    phrase: str
    sound: str
    style: str
    noise: float
    mess: float
    tag: str


@dataclass
class Truce:
    id: str
    label: str
    action: str
    payoff: str
    warmth: float


@dataclass
class World:
    venue: Venue
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


SETTINGS = {
    "barnyard": Venue(place="the barnyard", indoors=False, allows={"sound_show", "practice"}, acoustics="boomy"),
    "stage": Venue(place="the little stage", indoors=True, allows={"sound_show", "practice"}, acoustics="echoey"),
    "prairie": Venue(place="the prairie edge", indoors=False, allows={"sound_show"}, acoustics="wide"),
}

NOISEMAKERS = {
    "boing": Noisemaker(
        id="boing", label="a whatchamacallem", phrase="a squeaky whatchamacallem",
        sound="boing-boing", style="bounce", noise=1.0, mess=0.0, tag="boing",
    ),
    "vroom": Noisemaker(
        id="vroom", label="a whatchamacallem", phrase="a whirly whatchamacallem",
        sound="vroom-vroom", style="whirl", noise=1.0, mess=0.0, tag="vroom",
    ),
    "plink": Noisemaker(
        id="plink", label="a whatchamacallem", phrase="a tiny clattery whatchamacallem",
        sound="plink-plink", style="plink", noise=1.0, mess=0.0, tag="plink",
    ),
}

TRUCES = {
    "apology_cookie": Truce(
        id="apology_cookie", label="an apology cookie", action="share an apology cookie",
        payoff="the snack made the grumpy faces crack into smiles", warmth=1.0,
    ),
    "shared_giggle": Truce(
        id="shared_giggle", label="a shared giggle", action="tell the joke again",
        payoff="the second try was even sillier than the first", warmth=1.0,
    ),
    "tap_dance": Truce(
        id="tap_dance", label="a tiny tap dance", action="do a tiny tap dance",
        payoff="the beat helped them listen to each other", warmth=1.0,
    ),
}

BISON_NAMES = ["Benny", "Berta", "Boris", "Bina", "Brock", "Bubbles"]
PERSON_NAMES = ["Milo", "Maya", "Tess", "Otis", "Pia", "Ned"]
TRAITS = ["cheerful", "curious", "silly", "gentle", "mischievous", "dramatic"]


def make_bison_name(rng: random.Random) -> str:
    return rng.choice(BISON_NAMES)


def make_person_name(rng: random.Random) -> str:
    return rng.choice(PERSON_NAMES)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for venue_id, venue in SETTINGS.items():
        for n_id, n in NOISEMAKERS.items():
            for t_id, t in TRUCES.items():
                if venue.allows and n.noise >= THRESHOLD and t.warmth >= THRESHOLD:
                    combos.append((venue_id, n_id, t_id))
    return combos


@dataclass
class StoryParams:
    venue: str
    noise: str
    truce: str
    bison_name: str
    human_name: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny comedic storyworld about a bison, a whatchamacallem, sound effects, and reconciliation."
    )
    ap.add_argument("--venue", choices=SETTINGS)
    ap.add_argument("--noise", choices=NOISEMAKERS)
    ap.add_argument("--truce", choices=TRUCES)
    ap.add_argument("--bison-name")
    ap.add_argument("--human-name")
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


def explain_invalid(venue: Venue, noise: Noisemaker, truce: Truce) -> str:
    return (
        f"(No story: {venue.place} can host the noisy act, but this combination "
        f"doesn't leave a believable way for the bison and the whatchamacallem "
        f"to make up in a child-friendly, funny way.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.venue is None or c[0] == args.venue)
              and (args.noise is None or c[1] == args.noise)
              and (args.truce is None or c[2] == args.truce)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    venue_id, noise_id, truce_id = rng.choice(sorted(combos))
    return StoryParams(
        venue=venue_id,
        noise=noise_id,
        truce=truce_id,
        bison_name=args.bison_name or make_bison_name(rng),
        human_name=args.human_name or make_person_name(rng),
        trait=args.trait or rng.choice(TRAITS),
    )


def setup_world(params: StoryParams) -> World:
    world = World(venue=SETTINGS[params.venue])
    bison = world.add(Entity(id=params.bison_name, kind="character", type="bison", label="the bison", traits=[params.trait]))
    human = world.add(Entity(id=params.human_name, kind="character", type="human", label="the helper"))
    toy = world.add(Entity(
        id="whatchamacallem",
        kind="thing",
        type="whatchamacallem",
        label="whatchamacallem",
        phrase=NOISEMAKERS[params.noise].phrase,
        owner=bison.id,
    ))
    world.facts.update(bison=bison, human=human, toy=toy, noise=NOISEMAKERS[params.noise], truce=TRUCES[params.truce], params=params)
    return world


def intro(world: World) -> None:
    bison = world.facts["bison"]
    toy = world.facts["toy"]
    trait = bison.traits[0]
    world.say(f"{bison.id} was a {trait} bison who loved making a big entrance, even when the audience was very small.")
    world.say(f"{bison.id} also had {toy.phrase}, which made the funniest little sounds if anyone looked at it sideways.")


def build_up(world: World) -> None:
    bison = world.facts["bison"]
    human = world.facts["human"]
    noise = world.facts["noise"]
    venue = world.venue
    bison.memes["joy"] += 1
    world.say(f"One day, {bison.id} and {human.id} met at {venue.place}, where the air seemed made for silly echo games.")
    world.say(f"{bison.id} wanted to put on a little show, and {human.id} brought {world.facts['toy'].label} to help with sound effects.")
    world.say(f'When the act began, the whatchamacallem went "{noise.sound}!" and the whole place bounced with laughter.')


def conflict(world: World) -> None:
    bison = world.facts["bison"]
    human = world.facts["human"]
    toy = world.facts["toy"]
    bison.meters["noise"] += 1
    toy.meters["noise"] += 1
    human.memes["conflict"] += 1
    bison.memes["grump"] += 1
    world.say(f"But the noise was so dramatic that {human.id} covered {human.pronoun('object')} ears and said it sounded like a kettle wearing boots.")
    world.say(f"{bison.id} mistook that face for a complaint, huffed, and stamped so hard that the little stage felt even sillier.")
    world.say(f"Then the whatchamacallem rolled under a bench with a loud {world.facts['noise'].sound} that turned the moment into a comic mess.")


def reconcile(world: World) -> None:
    bison = world.facts["bison"]
    human = world.facts["human"]
    toy = world.facts["toy"]
    truce = world.facts["truce"]
    if bison.memes["grump"] < THRESHOLD:
        return
    bison.memes["shame"] += 1
    human.memes["warmth"] += 1
    world.say(f"After that, {bison.id} lowered {bison.pronoun('possessive')} head and snorted a tiny apology.")
    world.say(f'{human.id} smiled and said, "Let’s make the funny part on purpose."')
    world.say(f"They chose {truce.label} and decided to {truce.action}.")
    bison.memes["grump"] = 0.0
    bison.memes["warmth"] += truce.warmth
    human.memes["conflict"] = 0.0
    human.memes["warmth"] += truce.warmth
    toy.meters["noise"] = 0.0
    world.say(f"{truce.payoff.capitalize()}. Soon the whatchamacallem made a gentler sound, and the bison's snort came out like a giggle instead of a grumble.")
    world.say(f"By the end, {bison.id} and {human.id} were laughing together, with the whatchamacallem resting between them like a very proud clown nose.")


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    intro(world)
    world.para()
    build_up(world)
    conflict(world)
    world.para()
    reconcile(world)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short comedy story for children about {p.bison_name} the bison and a whatchamacallem that makes sound effects.",
        f"Tell a funny story where {p.bison_name} and {p.human_name} start with a noisy misunderstanding and end by making up.",
        f"Write a gentle, silly story set at {world.venue.place} with a bison, a whatchamacallem, and a reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    bison = world.facts["bison"]
    human = world.facts["human"]
    toy = world.facts["toy"]
    return [
        QAItem(
            question=f"Who made the biggest entrance in the story?",
            answer=f"{bison.id} the bison made the biggest entrance, because {bison.id} loved being dramatic and silly.",
        ),
        QAItem(
            question=f"What did the whatchamacallem do at {world.venue.place}?",
            answer=f"It made sound effects that went {world.facts['noise'].sound} and helped the little show feel lively.",
        ),
        QAItem(
            question=f"Why did {human.id} and {bison.id} need to make up?",
            answer=f"They had a funny misunderstanding after the sound effects got too loud, so they chose a kinder, calmer way to continue.",
        ),
        QAItem(
            question=f"How did the story end for {bison.id} and {human.id}?",
            answer=f"They ended up laughing together after using {world.facts['truce'].label}, so the grumpiness turned into a shared joke.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bison?",
            answer="A bison is a very large wild animal with a shaggy coat and a big, sturdy body.",
        ),
        QAItem(
            question="What is a whatchamacallem?",
            answer="A whatchamacallem is a made-up name for a thing when someone cannot quite remember its exact word.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special noises made on purpose to help a story, game, or show feel more lively.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making up after a disagreement so people can feel friendly again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:12} ({e.type:12}) meters={e.meters} memes={e.memes}")
    lines.append(f"  venue={world.venue.place} acoustics={world.venue.acoustics}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for vid, v in SETTINGS.items():
        lines.append(asp.fact("venue", vid))
        if v.indoors:
            lines.append(asp.fact("indoors", vid))
        for a in sorted(v.allows):
            lines.append(asp.fact("allows", vid, a))
    for nid, n in NOISEMAKERS.items():
        lines.append(asp.fact("noisemaker", nid))
        lines.append(asp.fact("sound", nid, n.sound))
        lines.append(asp.fact("noise_level", nid, int(n.noise * 10)))
    for tid, t in TRUCES.items():
        lines.append(asp.fact("truce", tid))
        lines.append(asp.fact("warmth_level", tid, int(t.warmth * 10)))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(V,N,T) :- venue(V), noisemaker(N), truce(T), allows(V,sound_show),
                      noise_level(N,L), L >= 10, warmth_level(T,W), W >= 10.
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    mapped = set((a, b, c) for a, b, c in clingo_set)
    if len(mapped) == len(python_set):
        print(f"OK: clingo gate matches valid_combos() ({len(mapped)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  clingo:", sorted(mapped))
    print("  python:", sorted(python_set))
    return 1


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
    StoryParams(venue="stage", noise="boing", truce="shared_giggle", bison_name="Benny", human_name="Milo", trait="silly"),
    StoryParams(venue="barnyard", noise="vroom", truce="apology_cookie", bison_name="Berta", human_name="Tess", trait="cheerful"),
    StoryParams(venue="prairie", noise="plink", truce="tap_dance", bison_name="Boris", human_name="Pia", trait="mischievous"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:")
        for v, n, t in combos:
            print(f"  {v:10} {n:8} {t:16}")
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
            except StoryError as err:
                print(err)
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
            header = f"### {p.bison_name}: {p.noise} at {p.venue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
