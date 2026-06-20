#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/polish_day_shy_friendship_inner_monologue_comedy.py
==================================================================================

A standalone story world sketch for a small comedy about friendship, a shy child,
and a very serious-looking "polish day" that turns out to be a tiny festival
of spoons, stickers, and awkward bravery.

Seed words:
- polish
- day
- shy

Features:
- Friendship
- Inner Monologue

Style:
- Comedy

This world simulates a little classroom or club-day cleanup where one shy child
worries about being seen, a friend notices the worry, and a goofy but concrete
task helps them both feel better. The inner monologue is not a frozen paragraph;
it is driven by changing emotional state, and the ending proves what changed:
the child goes from hiding behind a backpack to helping with a cheerful shared
polish-and-display moment.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/polish_day_shy_friendship_inner_monologue_comedy.py
    python storyworlds/worlds/gpt-5.4-mini/polish_day_shy_friendship_inner_monologue_comedy.py --all
    python storyworlds/worlds/gpt-5.4-mini/polish_day_shy_friendship_inner_monologue_comedy.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/polish_day_shy_friendship_inner_monologue_comedy.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/polish_day_shy_friendship_inner_monologue_comedy.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Scene:
    id: str
    place: str
    polish_target: str
    display_area: str
    reason: str
    props: str
    audience: str
    style: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PolishTask:
    id: str
    tool: str
    verb: str
    shine: str
    risk: int
    reward: int
    use_text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["shiny"] >= THRESHOLD and e.role == "hero":
            sig = ("relief", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["pride"] += 1
            e.memes["shy"] = max(0.0, e.memes["shy"] - 1.0)
            out.append("__relief__")
    return out


def _r_laughter(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["awkward"] < THRESHOLD:
            continue
        sig = ("laugh", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["comic_pressure"] += 1
        out.append("__laugh__")
    return out


CAUSAL_RULES = [
    Rule("relief", "social", _r_relief),
    Rule("laughter", "social", _r_laughter),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def reasonableness_gate(scene: Scene, task: PolishTask) -> bool:
    return "polish" in scene.tags and task.risk <= 3


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def predict_world(world: World, task: PolishTask) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get("hero"), task, narrate=False)
    return {
        "shiny": sim.get("object").meters["shiny"],
        "awkward": sim.get("hero").memes["awkward"],
    }


def _do_task(world: World, hero: Entity, task: PolishTask, narrate: bool = True) -> None:
    hero.meters["busy"] += 1
    hero.meters["shiny"] += 1
    hero.memes["focus"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, friend: Entity, scene: Scene) -> None:
    hero.memes["shy"] += 2
    friend.memes["warmth"] += 1
    world.say(
        f"It was {scene.id}, at {scene.place}, and {scene.props}. "
        f"{hero.id} and {friend.id} were helping with {scene.display_area} for {scene.audience}."
    )
    world.say(
        f"{hero.id} liked {scene.reason}, but {hero.pronoun('possessive')} heart kept trying to hide in {hero.label_word if hero.label else 'a pocket'}."
    )


def inner_monologue(world: World, hero: Entity) -> None:
    if hero.memes["shy"] >= 2:
        world.say(
            f'Inside, {hero.id} thought, "Please let me be useful and invisible at the same time."'
        )
    else:
        world.say(
            f'Inside, {hero.id} thought, "Maybe I can do one tiny brave thing without tripping over my own shoes."'
        )


def friend_notices(world: World, friend: Entity, hero: Entity) -> None:
    hero.memes["seen"] += 1
    world.say(
        f'{friend.id} noticed the quiet look on {hero.id}\'s face and said, "We can polish side by side. '
        f'You do not have to shine like a parade float."'
    )


def attempt(world: World, hero: Entity, task: PolishTask) -> None:
    hero.memes["awkward"] += 1
    world.say(
        f'{hero.id} picked up {task.tool} and tried to {task.verb}. '
        f'For a moment {hero.pronoun()} moved with very serious eyebrows.'
    )


def joke_moment(world: World, hero: Entity, friend: Entity, task: PolishTask) -> None:
    world.say(
        f'Then {friend.id} whispered, "If the spoon gets any shinier, it will start asking for a tiny hat."'
    )
    world.say(
        f'{hero.id} snorted. {hero.id} was still shy, but now the shyness had a giggle hiding inside it.'
    )


def finish(world: World, hero: Entity, friend: Entity, scene: Scene, task: PolishTask) -> None:
    hero.meters["shiny"] += 1
    world.get("object").meters["shiny"] = 2
    propagate(world, narrate=False)
    world.say(
        f"Together they finished the {scene.polish_target}, and the whole table gleamed like a happy moon."
    )
    world.say(
        f'{hero.id} looked at the tidy work, smiled a small brave smile, and thought, "I was shy, but I did it anyway."'
    )
    world.say(
        f'{friend.id} bumped shoulders with {hero.id}, and their friendship felt brighter than the polished {scene.polish_target}."
    )


def tell(scene: Scene, task: PolishTask, response: Response,
         hero_name: str = "Mina", hero_gender: str = "girl",
         friend_name: str = "Pip", friend_gender: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    obj = world.add(Entity(id="object", type="thing", label=scene.polish_target))
    world.facts["scene"] = scene
    world.facts["task"] = task
    world.facts["response"] = response

    setup(world, hero, friend, scene)
    world.para()
    inner_monologue(world, hero)
    friend_notices(world, friend, hero)
    attempt(world, hero, task)

    if reasonableness_gate(scene, task):
        world.para()
        joke_moment(world, hero, friend, task)
        if response.sense >= SENSE_MIN:
            finish(world, hero, friend, scene, task)
            outcome = "bright"
        else:
            outcome = "soft"
    else:
        world.say("No story: the task does not match the polish day setup.")
        outcome = "rejected"

    world.facts.update(hero=hero, friend=friend, object=obj, outcome=outcome)
    return world


SCENES = {
    "classroom": Scene("classroom", "the classroom", "the big silver tray", "the display shelf",
                       "the class wanted things to look welcoming", "paper stars and a half-finished banner",
                       "the whole room", "comedy", tags={"polish", "day", "friendship"}),
    "clubhouse": Scene("clubhouse", "the clubhouse", "the snack spoon", "the trophy shelf",
                       "the friends wanted the clubhouse to sparkle for visitors",
                       "a lot of crumbs, a tiny flag, and one dramatic spoon",
                       "the visitors", "comedy", tags={"polish", "day", "friendship"}),
    "kitchen": Scene("kitchen", "the kitchen", "the cookie tin", "the counter",
                     "the family wanted a shiny table for the afternoon tea",
                     "crumbs, napkins, and a lopsided fruit bowl",
                     "grandma", "comedy", tags={"polish", "day", "friendship"}),
}

TASKS = {
    "spoons": PolishTask("spoons", "a cloth", "polish the spoons", "very shiny", 1, 3,
                         "wiped the spoons until they glowed",
                         "rubbed the spoons, but they stayed dull",
                         "polished the spoons until they glowed",
                         tags={"polish"}),
    "tray": PolishTask("tray", "a soft towel", "polish the tray", "bright as a star", 2, 3,
                       "brought the tray to a bright shine",
                       "tried to polish the tray, but the cloth slipped around",
                       "polished the tray until it shone brightly",
                       tags={"polish"}),
    "trophy": PolishTask("trophy", "a tiny rag", "polish the trophy", "sparkly", 2, 2,
                         "made the trophy sparkle",
                         "polished the trophy, but only made a fuzzy face in the cloth",
                         "polished the trophy until it sparkled",
                         tags={"polish"}),
}

RESPONSES = {
    "laugh": Response("laugh", 3, 3,
                      "laughed, steadied the cloth, and helped keep the shine moving",
                      "laughed, but the polish day turned awkward and wobbly",
                      "laughed and helped the work stay on track",
                      tags={"comedy"}),
    "smile": Response("smile", 2, 2,
                      "smiled, took a breath, and kept polishing with a calmer hand",
                      "smiled weakly and forgot what to do next",
                      "smiled and kept polishing",
                      tags={"friendship"}),
    "tiny_cheer": Response("tiny_cheer", 2, 2,
                           "gave a tiny cheer and made the shiny part feel less scary",
                           "cheered too hard and nearly dropped the cloth",
                           "gave a tiny cheer and kept going",
                           tags={"comedy"}),
}

GIRL_NAMES = ["Mina", "Lina", "Nora", "Pia", "Ruby", "Tess"]
BOY_NAMES = ["Pip", "Otis", "Jules", "Ned", "Theo", "Ben"]
TRAITS = ["shy", "gentle", "careful", "quiet", "thoughtful"]


@dataclass
class StoryParams:
    scene: str
    task: str
    response: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SCENES:
        for t in TASKS:
            for r in RESPONSES:
                if reasonableness_gate(SCENES[s], TASKS[t]) and RESPONSES[r].sense >= SENSE_MIN:
                    combos.append((s, t, r))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A shy polish-day friendship comedy.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
              and (args.task is None or c[1] == args.task)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, task, response = rng.choice(sorted(combos))
    gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (BOY_NAMES + GIRL_NAMES) if n != hero])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(scene, task, response, hero, gender, friend, friend_gender, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene, task = f["scene"], f["task"]
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the words "polish", "day", and "shy".',
        f"Tell a friendship story where {f['hero'].id} feels shy on {scene.id} {scene.place} and helps with {task.verb}.",
        f"Write a comedy about two friends on {scene.id} polish day, with a shy inner monologue and a cheerful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, scene, task = f["hero"], f["friend"], f["scene"], f["task"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and {friend.id}, two friends helping on {scene.id}."
        ),
        QAItem(
            question=f"Why did {hero.id} feel shy?",
            answer=f"{hero.id} felt shy because {hero.pronoun('possessive')} mind wanted to help, but {hero.pronoun()} did not want to be watched too closely. The polishing job made {hero.id} worry about looking silly."
        ),
        QAItem(
            question="How did the friend help?",
            answer=f"{friend.id} noticed the shy look and stayed beside {hero.id}, making the work feel smaller and funnier. That friendly joke helped the polishing feel safe."
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"{hero.id} became brave enough to keep polishing and even smile at the finished shine. The friendship turned the shy moment into a funny shared success."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What does polish mean?",
            answer="To polish something means to rub it until it becomes smooth and shiny."
        ),
        QAItem(
            question="What is a shy feeling?",
            answer="Shy means feeling nervous or quiet around other people, like you want to hide a little."
        ),
        QAItem(
            question="What helps a friend feel less shy?",
            answer="A kind friend can help by staying close, speaking gently, and making the task feel easier."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("classroom", "spoons", "laugh", "Mina", "girl", "Pip", "boy", "shy"),
    StoryParams("clubhouse", "tray", "smile", "Theo", "boy", "Ruby", "girl", "quiet"),
    StoryParams("kitchen", "trophy", "tiny_cheer", "Nora", "girl", "Ben", "boy", "gentle"),
]


def explain_rejection() -> str:
    return "(No story: this combination does not fit a playful polish-day friendship scene.)"


ASP_RULES = r"""
valid(S,T,R) :- scene(S), task(T), response(R), risk(T, X), X <= 3, sense(R, N), N >= sense_min(M), N >= M.
outcome(bright) :- valid(_,_,_), not failed.
failed :- invalid_task.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SCENES.items():
        lines.append(asp.fact("scene", sid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("risk", tid, t.risk))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: generate smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], TASKS[params.task], RESPONSES[params.response],
                 params.hero_name, params.hero_gender, params.friend_name, params.friend_gender)
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
