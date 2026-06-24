#!/usr/bin/env python3
"""
A small adventure storyworld about a caper, a boss, and an aluminum clue.

The premise:
- A crew wants to complete a caper.
- Their boss sends them after an aluminum object that matters to the mission.
- A mystery blocks the way, but teamwork and foreshadowing help them solve it.

The world model tracks:
- physical meters: clue_progress, hush, wobble, shine, weight, trust_in_tool, etc.
- emotional memes: courage, worry, teamwork, curiosity, relief, respect, suspicion

The stories are simple, child-facing adventure tales with a beginning,
a turn, and a satisfying ending image.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    caper: str
    boss_order: str
    mystery: str
    clue: str
    foreshadow: str
    solve_method: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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
        clone = World(self.place)
        clone.entities = {k: Entity(
            id=v.id, kind=v.kind, type=v.type, label=v.label, phrase=v.phrase,
            plural=v.plural, owner=v.owner, caretaker=v.caretaker,
            meters=dict(v.meters), memes=dict(v.memes)
        ) for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def meme(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def bump_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = meter(entity, key) + amount


def bump_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = meme(entity, key) + amount


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for sent in _rule_mystery_deepens(world):
            if sent:
                out.append(sent)
                changed = True
        for sent in _rule_teamwork_solves(world):
            if sent:
                out.append(sent)
                changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def _rule_mystery_deepens(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    clue = world.get("clue")
    if meter(clue, "hidden") < THRESHOLD:
        return out
    sig = ("mystery",)
    if sig in world.fired:
        return out
    if meme(hero, "curiosity") < THRESHOLD:
        return out
    world.fired.add(sig)
    bump_meme(hero, "suspense", 1)
    out.append("The clue stayed hidden, and the mystery felt bigger for a moment.")
    return out


def _rule_teamwork_solves(world: World) -> list[str]:
    out: list[str] = []
    crew = [world.get(eid) for eid in ("hero", "friend", "boss") if eid in world.entities]
    if any(meme(e, "teamwork") < THRESHOLD for e in crew):
        return out
    clue = world.get("clue")
    boss = world.get("boss")
    if meter(clue, "found") >= THRESHOLD:
        return out
    sig = ("solve",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bump_meter(clue, "found", 1)
    bump_meme(boss, "pride", 1)
    out.append("Together, they spotted the hidden clue and solved the mystery.")
    return out


def predict_solve(world: World, hero: Entity, friend: Entity, boss: Entity, clue: Entity) -> dict:
    sim = world.copy()
    bump_meme(sim.get(hero.id), "teamwork", 1)
    bump_meme(sim.get(friend.id), "teamwork", 1)
    bump_meme(sim.get(boss.id), "teamwork", 1)
    bump_meme(sim.get(hero.id), "curiosity", 1)
    bump_meter(sim.get(clue.id), "hidden", 1)
    propagate(sim, narrate=False)
    return {
        "found": meter(sim.get(clue.id), "found") >= THRESHOLD,
        "pride": meme(sim.get(boss.id), "pride"),
    }


def tell(world: World, quest: Quest) -> None:
    hero = world.add(Entity(id="hero", kind="character", type="boy", label="Finn"))
    friend = world.add(Entity(id="friend", kind="character", type="girl", label="Mara"))
    boss = world.add(Entity(id="boss", kind="character", type="adult", label="Captain Vale"))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label="aluminum clue", phrase="a small aluminum clue"))
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label="aluminum hook", phrase="an aluminum hook"))

    bump_meter(clue, "hidden", 1)
    bump_meter(clue, "shine", 1)
    bump_meter(tool, "shine", 1)
    bump_meter(tool, "light", 1)
    bump_meme(hero, "curiosity", 1)
    bump_meme(friend, "curiosity", 1)
    bump_meme(boss, "calm", 1)

    world.facts.update(hero=hero, friend=friend, boss=boss, clue=clue, tool=tool, quest=quest)

    world.say(f"{hero.label} and {friend.label} were ready for a caper in {world.place.name}.")
    world.say(f"{boss.label} gave them a careful order: {quest.boss_order}")
    world.say(f"He pointed at {quest.clue} and warned that the aluminum hint would matter later.")
    world.say(f"{hero.label} noticed the shiny tool on the table, but did not know why it was there yet.")

    world.para()
    world.say(f"Inside {world.place.name}, the crew crept forward with soft steps.")
    world.say(f"{hero.label} wanted to solve the mystery fast, but the first door would not budge.")
    bump_meme(hero, "worry", 1)
    bump_meme(friend, "worry", 1)
    world.say(quest.foreshadow)

    world.para()
    world.say(f"{friend.label} remembered the aluminum hook and held it up to the light.")
    bump_meme(hero, "teamwork", 1)
    bump_meme(friend, "teamwork", 1)
    bump_meme(boss, "teamwork", 1)
    bump_meme(hero, "curiosity", 1)
    predict = predict_solve(world, hero, friend, boss, clue)
    if predict["found"]:
        world.say("That was the clue: the shine matched a tiny mark on the lock.")
    else:
        raise StoryError("The chosen quest does not lead to a solvable mystery.")

    world.say("They lifted, turned, and listened, each one helping in a different way.")
    propagate(world, narrate=True)

    world.para()
    bump_meter(clue, "found", 1)
    bump_meme(hero, "relief", 1)
    bump_meme(friend, "relief", 1)
    bump_meme(boss, "relief", 1)
    world.say(f"{quest.solve_method} Soon the mystery was solved, and the caper made sense at last.")
    world.say(f"{quest.ending_image} {boss.label} smiled because the team had worked together so well.")


QUESTS = {
    "harbor_lock": Quest(
        id="harbor_lock",
        caper="a midnight caper to open the harbor gate",
        boss_order="Find the aluminum clue and open the gate without waking the dock cats.",
        mystery="why the harbor gate had a strange little lock nobody could open",
        clue="the aluminum clue hiding under a crate",
        foreshadow="Earlier, a silver scratch on the map had hinted that metal would matter tonight.",
        solve_method="Finn held the hook, Mara guided the latch, and Captain Vale read the marks on the lock.",
        ending_image="The gate swung wide, and moonlight shimmered on the aluminum hook.",
        tags={"caper", "boss", "aluminum", "mystery", "teamwork", "foreshadowing"},
    ),
    "lantern_room": Quest(
        id="lantern_room",
        caper="a brave caper to find the lost lantern key",
        boss_order="Search the old room for the aluminum sign that tells where the key is hidden.",
        mystery="why a lantern kept going dark even when it had oil",
        clue="the aluminum tag tied to a dusty string",
        foreshadow="At the start, a tiny clink from the shelf had sounded like a warning.",
        solve_method="Mara lifted the tag, Finn followed the line, and together they found the key behind a panel.",
        ending_image="The lantern glowed again, and the aluminum tag flashed like a happy fish.",
        tags={"caper", "boss", "aluminum", "mystery", "teamwork", "foreshadowing"},
    ),
    "cave_map": Quest(
        id="cave_map",
        caper="a cave caper to find the missing map piece",
        boss_order="Bring back the aluminum marker before the tide turns the path wet.",
        mystery="where the missing map piece had gone inside the cave",
        clue="the aluminum marker tucked in a crack",
        foreshadow="A faint silver glint on the cave wall had looked strange from the very beginning.",
        solve_method="Finn and Mara held the lantern while Captain Vale used the marker to point out the hidden seam.",
        ending_image="The map piece slid free, and the aluminum marker sat bright in the lantern glow.",
        tags={"caper", "boss", "aluminum", "mystery", "teamwork", "foreshadowing"},
    ),
}

PLACES = {
    "harbor": Place(name="the harbor", tags={"adventure", "water"}),
    "old_room": Place(name="the old room", indoors=True, tags={"adventure", "indoor"}),
    "cave": Place(name="the cave", tags={"adventure", "dark"}),
}

CURATED = [
    ("harbor", "harbor_lock"),
    ("old_room", "lantern_room"),
    ("cave", "cave_map"),
]


@dataclass
class StoryParams:
    place: str
    quest: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: caper, boss, aluminum, teamwork, and mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
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
    combos = CURATED
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest = rng.choice(combos)
    return StoryParams(place=place, quest=quest)


def generate(params: StoryParams) -> StorySample:
    world = World(place=PLACES[params.place])
    quest = QUESTS[params.quest]
    tell(world, quest)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    q = world.facts["quest"]
    return [
        f'Write a short adventure story about "{q.caper}" that includes teamwork and a hidden aluminum clue.',
        f"Tell a child-friendly mystery where a boss gives a caper order and the crew solves it together.",
        f'Write a story that foreshadows a solution with something shiny and ends with the mystery solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    q: Quest = world.facts["quest"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    boss = world.facts["boss"]
    clue = world.facts["clue"]
    return [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about {hero.label} and {friend.label}, who worked with {boss.label} on a caper.",
        ),
        QAItem(
            question="What did the boss want them to find?",
            answer=f"{boss.label} wanted them to find {q.clue}, because the aluminum clue would help solve the mystery.",
        ),
        QAItem(
            question="What solved the mystery?",
            answer=f"They solved it with teamwork, by using the aluminum tool and following the foreshadowed hint.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {q.ending_image}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is aluminum?",
            answer="Aluminum is a light metal that can shine and is often used for tools, cans, and parts that need to stay sturdy without being heavy.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other, share jobs, and solve a problem together.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue or hint that appears early in a story and helps you guess what will matter later.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or secret that characters need to figure out.",
        ),
    ]


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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id}: {e.label or e.type} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for tag in sorted(place.tags):
            lines.append(asp.fact("place_tag", pid, tag))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("contains", qid, "caper"))
        lines.append(asp.fact("contains", qid, "boss"))
        lines.append(asp.fact("contains", qid, "aluminum"))
        for tag in sorted(q.tags):
            lines.append(asp.fact("tagged", qid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,Q) :- place(P), quest(Q), tagged(Q, teamwork), tagged(Q, foreshadowing), tagged(Q, mystery).
needs_aluminum(Q) :- quest(Q), contains(Q, aluminum).
adventure_story(P,Q) :- valid_story(P,Q), needs_aluminum(Q).
#show valid_story/2.
#show adventure_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, q) for p, q in CURATED}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches curated valid stories ({len(cl)}).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show adventure_story/2.\n#show valid_story/2."))
        pairs = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(pairs)} valid stories:")
        for p, q in pairs:
            print(f"  {p} {q}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for place, quest in CURATED:
            params = StoryParams(place=place, quest=quest, seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.place} / {p.quest}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
