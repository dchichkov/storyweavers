#!/usr/bin/env python3
"""
storyworlds/worlds/english_humor_conflict_surprise_pirate_tale.py
===================================================================

A small classical story world in a pirate-tale style with humor, conflict,
and surprise. The story is generated from a simulated world model with typed
entities, physical meters, and emotional memes.

Seed premise:
A cheerful pirate wants to use a map and a small clever trick to find a prize,
but a grumpy shipmate suspects a mistake. The argument turns funny when the
"monster" turns out to be something silly, and the crew resolves the conflict
with a shared discovery.
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
    kind: str = "thing"          # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "captain"}
        male = {"boy", "man", "father", "dad", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Scene:
    place: str = "the ship"
    place_word: str = "ship"
    action: str = "sail"
    weather: str = "breezy"
    afford: set[str] = field(default_factory=set)


@dataclass
class Plot:
    id: str
    verb: str
    gerund: str
    surprise: str
    rumor: str
    risk: str
    clue: str
    outcome: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    value: str
    plural: bool = False


@dataclass
class Trick:
    id: str
    label: str
    prep: str
    reveal: str
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def bump_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = meter(ent, key) + amt


def bump_meme(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = meme(ent, key) + amt


def say_name(ent: Entity) -> str:
    return ent.label or ent.id


def rule_fuss(world: World) -> list[str]:
    out: list[str] = []
    for ch in world.characters():
        if meme(ch, "grumble") >= THRESHOLD and meme(ch, "confused") >= THRESHOLD:
            sig = ("fuss", ch.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            bump_meme(ch, "conflict", 1.0)
            out.append(f"{say_name(ch)} started to fuss like a gull with a sore toe.")
    return out


def rule_laugh(world: World) -> list[str]:
    out: list[str] = []
    for ch in world.characters():
        if meter(ch, "silly") >= THRESHOLD and meme(ch, "conflict") >= THRESHOLD:
            sig = ("laugh", ch.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            bump_meme(ch, "joy", 1.0)
            out.append(f"Then even {say_name(ch)} had to laugh.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (rule_fuss, rule_laugh):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_reveal(world: World, crew: Entity, plot: Plot, trick: Trick, prize: Prize) -> dict:
    sim = world.copy()
    sailor = sim.get(crew.id)
    bump_meme(sailor, "confused", 1.0)
    bump_meter(sailor, "silly", 1.0)
    return {
        "conflict": True,
        "surprise": True,
        "humor": True,
    }


def intro(world: World, hero: Entity, mate: Entity, plot: Plot, prize: Prize) -> None:
    world.say(
        f"{say_name(hero)} was a cheerful pirate who loved a good {plot.verb} and a shiny {prize.label}."
    )
    world.say(
        f"{say_name(mate)} was the sort of shipmate who frowned at every odd squeak in the boards."
    )


def setup(world: World, hero: Entity, mate: Entity, plot: Plot, prize: Prize) -> None:
    bump_meme(hero, "curious", 1.0)
    bump_meme(hero, "joy", 1.0)
    prize.owner = hero.id
    prize.held_by = hero.id
    world.say(
        f"One breezy morning, they sailed on {world.scene.place} with a {prize.phrase} tucked near the mast."
    )
    world.say(
        f"{say_name(hero)} wanted to {plot.verb}, because the map promised {plot.risk} and a funny little clue."
    )


def warning(world: World, hero: Entity, mate: Entity, plot: Plot, prize: Prize) -> None:
    bump_meme(mate, "grumble", 1.0)
    bump_meme(mate, "confused", 1.0)
    world.say(
        f"{say_name(mate)} squinted at the map and said, "
        f"\"That mark looks wrong. It might lead us to {plot.surprise}.\""
    )
    world.say(
        f"{say_name(hero)} replied, \"A pirate adventure needs a little silliness!\""
    )


def conflict(world: World, hero: Entity, mate: Entity, plot: Plot, prize: Prize) -> None:
    bump_meme(mate, "conflict", 1.0)
    bump_meme(hero, "conflict", 1.0)
    world.say(
        f"{say_name(mate)} blocked the hatch, and the two pirates bickered like parrots over a cracker."
    )
    world.say(
        f"Then {say_name(hero)} followed the clue anyway, hoping it was not a great mistake."
    )


def surprise_turn(world: World, hero: Entity, mate: Entity, plot: Plot, trick: Trick, prize: Prize) -> None:
    bump_meter(hero, "silly", 1.0)
    bump_meter(mate, "silly", 1.0)
    bump_meme(hero, "surprised", 1.0)
    bump_meme(mate, "surprised", 1.0)
    world.say(
        f"At the end of the trail, the fearsome \"monster\" turned out to be {plot.surprise}."
    )
    world.say(
        f"It was so unexpected that even the grumpiest pirate snorted with laughter."
    )
    world.say(
        f"{trick.reveal} {say_name(hero)} had used {trick.label}, and the trick had led them straight to the prize."
    )


def resolution(world: World, hero: Entity, mate: Entity, prize: Prize) -> None:
    bump_meme(hero, "joy", 1.0)
    bump_meme(mate, "joy", 1.0)
    hero.memes["conflict"] = 0.0
    mate.memes["conflict"] = 0.0
    world.say(
        f"The two pirates shared the {prize.label}, and the whole ship felt lighter than a feather in a sea breeze."
    )
    world.say(
        f"By sunset, {say_name(hero)} was laughing, {say_name(mate)} was smiling, and the map's silly mistake had become their best story."
    )


def tell(scene: Scene, plot: Plot, prize: Prize, trick: Trick,
         hero_name: str, mate_name: str) -> World:
    world = World(scene)
    hero = world.add(Entity(id=hero_name, kind="character", type="pirate", label=hero_name))
    mate = world.add(Entity(id=mate_name, kind="character", type="pirate", label=mate_name))
    treasure = world.add(Entity(id="prize", type=prize.type, label=prize.label, phrase=prize.phrase, plural=prize.plural))
    world.facts["hero"] = hero
    world.facts["mate"] = mate
    world.facts["prize"] = treasure
    world.facts["plot"] = plot
    world.facts["trick"] = trick

    intro(world, hero, mate, plot, treasure)
    world.para()
    setup(world, hero, mate, plot, treasure)
    warning(world, hero, mate, plot, treasure)
    conflict(world, hero, mate, plot, treasure)
    world.para()
    surprise_turn(world, hero, mate, plot, trick, treasure)
    propagate(world, narrate=True)
    resolution(world, hero, mate, treasure)
    return world


SCENES = {
    "ship": Scene(place="the ship", place_word="ship", action="sail", weather="breezy", afford={"map", "search"}),
    "island": Scene(place="the island", place_word="island", action="explore", weather="sunny", afford={"map", "search"}),
    "cove": Scene(place="the cove", place_word="cove", action="search", weather="windy", afford={"map", "search"}),
}

PLOTS = {
    "map": Plot(
        id="map",
        verb="follow the map",
        gerund="following the map",
        surprise="a crab wearing the captain's tiny hat",
        rumor="a chest under the rocks",
        risk="a splashy surprise",
        clue="a dotted line",
        outcome="the map was a joke with a real treasure hidden in it",
        tags={"humor", "surprise", "conflict"},
    ),
    "squeak": Plot(
        id="squeak",
        verb="chase the squeak",
        gerund="chasing the squeak",
        surprise="the ship's parrot hiding in a barrel",
        rumor="a ghost in the hold",
        risk="a spooky sound",
        clue="a feather trail",
        outcome="the scary sound was only a silly bird",
        tags={"humor", "surprise", "conflict"},
    ),
    "spark": Plot(
        id="spark",
        verb="follow the spark",
        gerund="following the spark",
        surprise="a lantern swinging on a rope",
        rumor="a sea sprite",
        risk="a bright trick of light",
        clue="a shining hook mark",
        outcome="the mystery light led to a buried tin cup of coins",
        tags={"humor", "surprise", "conflict"},
    ),
}

PRIZES = {
    "coins": Prize(id="coins", label="coins", phrase="a pocketful of coins", type="coins", value="gold", plural=True),
    "cup": Prize(id="cup", label="cup", phrase="a tiny silver cup", type="cup", value="silver"),
    "pearls": Prize(id="pearls", label="pearls", phrase="a string of pearls", type="pearls", value="pearls", plural=True),
}

TRICKS = {
    "laugh": Trick(id="laugh", label="a wink and a whistle", prep="with", reveal="As it turned out,",
                   helps={"map", "squeak", "spark"}),
    "lantern": Trick(id="lantern", label="a lantern held under the map", prep="with", reveal="When the light shone through it,",
                     helps={"map", "spark"}),
    "sneeze": Trick(id="sneeze", label="a fake sneeze to startle the crew", prep="with", reveal="After the sneeze,",
                    helps={"squeak"}),
}

HERO_NAMES = ["Ari", "Beck", "Nico", "Mina", "Jo", "Tess"]
MATE_NAMES = ["Grit", "Bram", "Lark", "Pip", "Moss", "Rook"]


@dataclass
class StoryParams:
    scene: str
    plot: str
    prize: str
    trick: str
    hero_name: str
    mate_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for scene_id, scene in SCENES.items():
        for plot_id in scene.afford:
            for prize_id in PRIZES:
                for trick_id, trick in TRICKS.items():
                    if plot_id in trick.helps:
                        combos.append((scene_id, plot_id, prize_id, trick_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate tale for a child that includes the word "english" and ends with a funny surprise.',
        f"Tell a humorous pirate story where {f['hero'].id} and {f['mate'].id} argue over a map, then discover that the scary thing is silly.",
        f"Write a simple sea adventure about a crew on {world.scene.place} where a trick turns conflict into laughter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    prize = f["prize"]
    plot = f["plot"]
    trick = f["trick"]
    return [
        QAItem(
            question=f"Who wanted to {plot.verb} on {world.scene.place}?",
            answer=f"{hero.id} wanted to {plot.verb} because the map promised a clever adventure.",
        ),
        QAItem(
            question=f"Why did {mate.id} get upset during the trip?",
            answer=f"{mate.id} got upset because the map looked wrong and seemed to point toward {plot.surprise}.",
        ),
        QAItem(
            question=f"What was the surprise at the end of the story?",
            answer=f"The surprise was {plot.surprise}, and it turned the spooky worry into laughter.",
        ),
        QAItem(
            question=f"How did the crew fix the argument?",
            answer=f"They used {trick.label} and followed the clue together, so the fight ended and they found the prize.",
        ),
        QAItem(
            question=f"What did they bring home?",
            answer=f"They brought home {prize.phrase}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a map for?",
            answer="A map is a picture that helps people find where to go.",
        ),
        QAItem(
            question="Why can pirates laugh during a tricky moment?",
            answer="People can laugh when a strange mistake turns out to be harmless or silly.",
        ),
        QAItem(
            question="What does surprise mean?",
            answer="A surprise is something you did not expect to happen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: the chosen pirate setup does not support a reasonable conflict-to-surprise turn.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Humorous pirate tale story world.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--plot", choices=PLOTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--mate-name", choices=MATE_NAMES)
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
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.plot is None or c[1] == args.plot)
              and (args.prize is None or c[2] == args.prize)
              and (args.trick is None or c[3] == args.trick)]
    if not combos:
        raise StoryError(explain_rejection())
    scene, plot, prize, trick = rng.choice(sorted(combos))
    return StoryParams(
        scene=scene,
        plot=plot,
        prize=prize,
        trick=trick,
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        mate_name=args.mate_name or rng.choice(MATE_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], PLOTS[params.plot], PRIZES[params.prize],
                 TRICKS[params.trick], params.hero_name, params.mate_name)
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
scene(S) :- setting(S).
plot(P) :- story_plot(P).
prize(R) :- treasure(R).
trick(T) :- trick(T).

compatible(S,P,R,T) :- setting(S), story_plot(P), treasure(R), trick(T),
                       affords(S,P), helps(T,P).

#show compatible/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SCENES.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for pid in PLOTS:
        lines.append(asp.fact("story_plot", pid))
    for rid in PRIZES:
        lines.append(asp.fact("treasure", rid))
    for tid, t in TRICKS.items():
        lines.append(asp.fact("trick", tid))
        for p in sorted(t.helps):
            lines.append(asp.fact("helps", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/4."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for scene_id, plot_id, prize_id, trick_id in sorted(valid_combos()):
            params = StoryParams(
                scene=scene_id,
                plot=plot_id,
                prize=prize_id,
                trick=trick_id,
                hero_name=HERO_NAMES[0],
                mate_name=MATE_NAMES[0],
            )
            samples.append(generate(params))
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
            header = f"### {p.hero_name}: {p.plot} on {p.scene}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
