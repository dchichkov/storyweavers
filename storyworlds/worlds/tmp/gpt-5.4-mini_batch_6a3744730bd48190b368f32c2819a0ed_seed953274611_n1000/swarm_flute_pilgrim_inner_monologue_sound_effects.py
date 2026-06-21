#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/swarm_flute_pilgrim_inner_monologue_sound_effects.py
====================================================================================

A small standalone storyworld about a pilgrim, a flute, and a buzzing swarm.

Premise:
A pilgrim carrying a flute must cross a flower path where a swarm of bees
blocks the way. The pilgrim thinks aloud, tests a calming tune, and learns that
soft music and careful steps can guide living things more gently than panic.

The world is built for a rhyming, child-facing story style with:
- inner monologue
- sound effects
- a state-driven turn and ending image

The simulated state tracks both physical meters and emotional memes:
- meters: swarm agitation, flute play, travel progress, bee pollen, path safety
- memes: fear, calm, courage, wonder, relief

The story is not a frozen paragraph with swapped nouns; the prose is driven by
the world state as the beats unfold.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad", "pilgrim"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Path:
    id: str
    label: str
    place: str
    flowers: str
    shelter: str
    scent: str
    pollen_rich: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Flute:
    id: str
    label: str
    phrase: str
    tone: str
    soft: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Swarm:
    id: str
    label: str
    buzz: str
    sting_threat: str
    likes_music: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    path: str
    flute: str
    swarm: str
    action: str
    pilgrim_name: str = "Pip"
    pilgrim_type: str = "pilgrim"
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
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

    def copy(self) -> "World":
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    pilgrim = world.get("pilgrim")
    swarm = world.get("swarm")
    if pilgrim.meters["calm_music"] >= THRESHOLD and swarm.meters["agitated"] >= THRESHOLD:
        sig = ("settle",)
        if sig not in world.fired:
            world.fired.add(sig)
            swarm.meters["agitated"] = max(0.0, swarm.meters["agitated"] - 1)
            swarm.memes["calm"] += 1
            out.append("The buzzing softened into a sleepy hum.")
    return out


def _r_clear_path(world: World) -> list[str]:
    out: list[str] = []
    pilgrim = world.get("pilgrim")
    path = world.get("path")
    swarm = world.get("swarm")
    if pilgrim.meters["calm_music"] >= THRESHOLD and swarm.meters["agitated"] < THRESHOLD:
        sig = ("clear",)
        if sig not in world.fired:
            world.fired.add(sig)
            path.meters["safe"] += 1
            out.append("The flower path opened like a ribbon of light.")
    return out


CAUSAL_RULES = [_r_settle, _r_clear_path]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(flute: Flute, swarm: Swarm, action: Action) -> bool:
    return flute.soft and swarm.likes_music and action.sense >= 2


def action_power(action: Action, swirl_delay: int) -> int:
    return action.power - swirl_delay


def action_succeeds(action: Action, swirl_delay: int) -> bool:
    return action_power(action, swirl_delay) >= 2


def predict(world: World, action: Action, swirl_delay: int) -> dict:
    sim = world.copy()
    perform(sim, sim.get("pilgrim"), sim.get("flute"), sim.get("swarm"), sim.get("path"), action, swirl_delay, narrate=False)
    return {
        "settled": sim.get("swarm").meters["agitated"] < THRESHOLD,
        "safe": sim.get("path").meters["safe"] >= THRESHOLD,
    }


def perform(world: World, pilgrim: Entity, flute: Entity, swarm: Entity, path: Entity,
            action: Action, swirl_delay: int, narrate: bool = True) -> None:
    pilgrim.meters["travel"] += 1
    pilgrim.memes["courage"] += 1
    flute.meters["played"] += 1
    pilgrim.meters["calm_music"] += 1
    swarm.meters["agitated"] += 1
    swarm.meters["buzz"] += 1
    if narrate:
        world.say(f"{pilgrim.id} took a breath and thought, \"{action.text}\"")
        world.say(f"Ffft-foo! {flute.label} sang {flute.tone}, and the swarm answered: {swarm.buzz}")
    if action_succeeds(action, swirl_delay):
        swarm.meters["agitated"] = max(0.0, swarm.meters["agitated"] - 1)
    else:
        swarm.meters["agitated"] += 1
    propagate(world, narrate=narrate)


def tell(path: Path, flute: Flute, swarm: Swarm, action: Action,
         pilgrim_name: str = "Pip", pilgrim_type: str = "pilgrim",
         swirl_delay: int = 0, weather: str = "bright") -> World:
    world = World()
    pilgrim = world.add(Entity(id="pilgrim", kind="character", type=pilgrim_type, label=pilgrim_name))
    p = world.add(Entity(id="path", type="path", label=path.label, attrs={"place": path.place}, tags=set(path.tags)))
    f = world.add(Entity(id="flute", type="flute", label=flute.label, attrs={"tone": flute.tone}, tags=set(flute.tags)))
    s = world.add(Entity(id="swarm", type="swarm", label=swarm.label, attrs={"shelter": path.shelter}, tags=set(swarm.tags)))

    pilgrim.memes["wonder"] += 1
    pilgrim.memes["fear"] += 0.5
    s.meters["agitated"] = 1.0
    p.meters["distance"] = 3.0

    world.say(
        f"Along a {weather} pilgrim way, {pilgrim.id} walked with {flute.phrase} tucked near {pilgrim.pronoun('possessive')} heart."
    )
    world.say(
        f"The lane smelled of {path.scent}, and a {swarm.label} swayed above the {path.flowers} with {swarm.sting_threat} in its hum."
    )
    world.say(
        f"{pilgrim.id} thought, \"If I rush, I may lose my tune. If I tremble, I may lose my way.\""
    )

    world.para()
    world.say(f"Then came the sound: {swarm.buzz}!")
    world.say(f"{pilgrim.id} whispered, \"My feet feel small, but my song can be kind.\"")
    perform(world, pilgrim, f, s, p, action, swirl_delay, narrate=True)

    if p.meters["safe"] >= THRESHOLD:
        world.para()
        pilgrim.memes["relief"] += 1
        pilgrim.memes["joy"] += 1
        world.say(
            f"The swarm drifted to the {path.shelter}, and the path turned soft and clear."
        )
        world.say(
            f"{pilgrim.id} smiled and said, \"I stepped with care, and the day did not dare.\""
        )
        world.say(
            f"With flute-tune afloat, {pilgrim.id} went on, a pilgrim in peace, light as a feather, bright as a song."
        )
    else:
        world.para()
        pilgrim.memes["fear"] += 1
        world.say(
            f"The buzzing stayed loud, so {pilgrim.id} paused beneath the {path.shelter} and played again, slow and proud."
        )
        world.say(
            f"At last the swarm loosened its stormy cloud, and {pilgrim.id} crossed with a quieter crowd."
        )

    world.facts.update(
        pilgrim=pilgrim,
        path=path,
        flute=flute,
        swarm=swarm,
        action=action,
        swirl_delay=swirl_delay,
        outcome="safe" if p.meters["safe"] >= THRESHOLD else "gentle_pause",
        weather=weather,
    )
    return world


PATHS = {
    "hillroad": Path(
        id="hillroad",
        label="hill road",
        place="the hill road",
        flowers="wildflowers",
        shelter="stone arch",
        scent="thyme",
        tags={"path", "flowers"},
    ),
    "garden_lane": Path(
        id="garden_lane",
        label="garden lane",
        place="the garden lane",
        flowers="rose blooms",
        shelter="hedge",
        scent="mint",
        tags={"path", "flowers"},
    ),
    "orchard_walk": Path(
        id="orchard_walk",
        label="orchard walk",
        place="the orchard walk",
        flowers="apple blossoms",
        shelter="apple tree",
        scent="sweet grass",
        tags={"path", "flowers"},
    ),
}

FLUTES = {
    "reed": Flute(id="reed", label="reed flute", phrase="a reed flute", tone="soft and round", tags={"flute", "music"}),
    "silver": Flute(id="silver", label="silver flute", phrase="a silver flute", tone="clear as moonlight", tags={"flute", "music"}),
    "wood": Flute(id="wood", label="wood flute", phrase="a wood flute", tone="warm and low", tags={"flute", "music"}),
}

SWARMS = {
    "bees": Swarm(id="bees", label="swarm of bees", buzz="bzz-bzz-bzz", sting_threat="tiny stings", tags={"swarm", "bees"}),
    "moths": Swarm(id="moths", label="swarm of moths", buzz="frrr-frrr-frrr", sting_threat="dusty wings", likes_music=True, tags={"swarm"}),
}

ACTIONS = {
    "hum": Action(id="hum", sense=3, power=3, text="Maybe a soft tune will calm the air.", fail="tried to hum, but the fear stayed near", qa_text="played a soft tune to calm the swarm", tags={"music", "calm"}),
    "call": Action(id="call", sense=2, power=2, text="I can play a brave little note and keep my feet slow.", fail="played too fast, and the swarm grew bold", qa_text="played a brave little note to keep moving", tags={"music", "calm"}),
    "lullaby": Action(id="lullaby", sense=4, power=4, text="A lullaby may turn buzzing to rest.", fail="played too loudly, and the air got upset", qa_text="played a lullaby to settle the buzzing", tags={"music", "calm"}),
}

CURATED = [
    StoryParams(path="hillroad", flute="reed", swarm="bees", action="hum", pilgrim_name="Pip", pilgrim_type="pilgrim"),
    StoryParams(path="garden_lane", flute="silver", swarm="bees", action="lullaby", pilgrim_name="Mira", pilgrim_type="pilgrim"),
    StoryParams(path="orchard_walk", flute="wood", swarm="moths", action="call", pilgrim_name="Tess", pilgrim_type="pilgrim"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PATHS:
        for f in FLUTES:
            for s in SWARMS:
                for a in ACTIONS:
                    if reasonableness_gate(FLUTES[f], SWARMS[s], ACTIONS[a]):
                        out.append((p, f, s, a))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: a pilgrim, a flute, and a swarm.")
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--flute", choices=FLUTES)
    ap.add_argument("--swarm", choices=SWARMS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--name")
    ap.add_argument("--type", default="pilgrim")
    ap.add_argument("--delay", type=int, default=0)
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
    if args.path and args.flute and args.swarm and args.action:
        if not reasonableness_gate(FLUTES[args.flute], SWARMS[args.swarm], ACTIONS[args.action]):
            raise StoryError("That flute, swarm, and action do not make a sensible calming story.")
    combos = [c for c in valid_combos()
              if (args.path is None or c[0] == args.path)
              and (args.flute is None or c[1] == args.flute)
              and (args.swarm is None or c[2] == args.swarm)
              and (args.action is None or c[3] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    path, flute, swarm, action = rng.choice(sorted(combos))
    return StoryParams(
        path=path,
        flute=flute,
        swarm=swarm,
        action=action,
        pilgrim_name=args.name or rng.choice(["Pip", "Mira", "Tess", "Ivo", "Nia"]),
        pilgrim_type=args.type,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.path not in PATHS or params.flute not in FLUTES or params.swarm not in SWARMS or params.action not in ACTIONS:
        raise StoryError("Invalid parameters for this storyworld.")
    world = tell(PATHS[params.path], FLUTES[params.flute], SWARMS[params.swarm], ACTIONS[params.action], params.pilgrim_name, params.pilgrim_type, swirl_delay=params.seed or 0)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a child about a {f["swarm"].label} and a {f["pilgrim"].label}, with a flute and sound effects.',
        f"Tell a gentle story where {f['pilgrim'].id} thinks to use {f['flute'].label} music to calm a {f['swarm'].label}.",
        "Write a child-friendly rhyming story with inner monologue and buzzing sound effects.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    p = f["pilgrim"]
    return [
        ("Who is the story about?", f"It is about {p.id}, a pilgrim who walks with a flute and meets a buzzing swarm."),
        ("What did the pilgrim think?", "The pilgrim thought that a soft tune might help. That calm idea guided the next step instead of panic."),
        ("How did the story end?", "The buzzing turned gentler, and the pilgrim continued on the path. The ending shows that careful music and patient steps changed the moment."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("What does a flute do?", "A flute makes music when someone blows across it and fingers its holes. In a story, it can help set a calm mood."),
        ("What is a swarm?", "A swarm is a large group of small living things moving together. Bees often swarm when they cluster and buzz around one place."),
        ("What is a pilgrim?", "A pilgrim is someone traveling to a special place, often with care and purpose. In stories, pilgrims are often quiet walkers on a long road."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PATHS:
        lines.append(asp.fact("path", pid))
    for fid in FLUTES:
        lines.append(asp.fact("flute", fid))
        lines.append(asp.fact("soft", fid))
    for sid in SWARMS:
        lines.append(asp.fact("swarm", sid))
        lines.append(asp.fact("likes_music", sid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, a.sense))
        lines.append(asp.fact("power", aid, a.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(P,F,S,A) :- path(P), flute(F), swarm(S), action(A), soft(F), likes_music(S), sense(A,X), sense_min(M), X >= M.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/4."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        rc = 1
        print("MISMATCH: ASP and Python disagree.")
        print("only python:", sorted(py - cl))
        print("only asp:", sorted(cl - py))
    else:
        print(f"OK: gate matches ({len(py)} combos).")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"FAIL: generate() smoke test crashed: {e}")
        return 1
    return rc


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("---- trace ----")
        for e in sample.world.entities.values():
            print(e.id, dict(e.meters), dict(e.memes), e.tags)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
                params.seed = base_seed + i
                sample = generate(params)
            except StoryError as e:
                print(e)
                return
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], ensure_ascii=False, indent=2))
        return
    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {idx+1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
