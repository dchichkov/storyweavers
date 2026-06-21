#!/usr/bin/env python3
"""
storyworlds/worlds/bouncer_pot_peekaboo_dialogue_fable.py
==========================================================

A small storyworld about a proud bouncer, a tricky pot, and a game of peekaboo.

Seed premise:
A child tries to hide in a big pot and play peekaboo at the town gate. The
bouncer notices, warns them with dialogue, and the child learns that good
games need safe places. The ending should feel like a little fable: the wiser
choice is kinder than the risky one.

This world keeps the simulation simple:
- typed entities with physical meters and emotional memes
- a short causal chain driven by state, not by frozen prose
- dialogue in the rendered story
- a Python reasonableness gate and an inline ASP twin
- three QA sets grounded in the simulated world

Run:
    python storyworlds/worlds/bouncer_pot_peekaboo_dialogue_fable.py
    python storyworlds/worlds/bouncer_pot_peekaboo_dialogue_fable.py --qa
    python storyworlds/worlds/bouncer_pot_peekaboo_dialogue_fable.py --verify
"""

from __future__ import annotations

import argparse
import copy
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
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    label: str
    scene: str
    place_detail: str


@dataclass
class Game:
    id: str
    title: str
    trick: str
    safe_place: str


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    risky_if_hidden: bool
    risky_if_play: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    game: str
    object_cfg: str
    response: str
    child_name: str
    child_gender: str
    bouncer_name: str
    bouncer_gender: str
    parent_name: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        c.facts = copy.deepcopy(self.facts)
        return c


SETTINGS = {
    "gate": Setting("gate", "the town gate", "the gate square", "beside the old stone wall"),
    "market": Setting("market", "the market gate", "the market square", "under the striped awning"),
}

GAMES = {
    "peekaboo": Game("peekaboo", "peekaboo", "hide and pop out", "behind a tree"),
    "hideout": Game("hideout", "hideout", "hide and surprise", "under a blanket"),
}

OBJECTS = {
    "pot": ObjectCfg("pot", "pot", "a big clay pot", True, True, tags={"pot", "hide"}),
    "barrel": ObjectCfg("barrel", "barrel", "a wooden barrel", True, True, tags={"barrel", "hide"}),
    "basket": ObjectCfg("basket", "basket", "a wicker basket", True, False, tags={"basket", "hide"}),
}

RESPONSES = {
    "lift": Response("lift", 3, 3, "lifted the pot carefully and set it aside", "tried to lift the pot, but it was too heavy", tags={"lift"}),
    "roll": Response("roll", 3, 2, "rolled the pot away with both hands", "tried to roll the pot, but it wobbled and stayed put", tags={"roll"}),
    "call": Response("call", 2, 1, "called for another grown-up and kept the child safe", "called for help, but the help came too slowly", tags={"call"}),
}

GIRL_NAMES = ["Mina", "Lena", "Tia", "Nora", "Ivy", "Pia"]
BOY_NAMES = ["Oren", "Tomo", "Jace", "Milo", "Eli", "Perry"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for gid in GAMES:
            for oid, obj in OBJECTS.items():
                if gid == "peekaboo" and obj.risky_if_hidden:
                    combos.append((sid, gid, oid))
                if gid == "hideout" and obj.risky_if_play:
                    combos.append((sid, gid, oid))
    return combos


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def reasonableness_gate(game: Game, obj: ObjectCfg) -> bool:
    return (game.id == "peekaboo" and obj.risky_if_hidden) or (game.id == "hideout" and obj.risky_if_play)


def response_outcome(response: Response, delay: int) -> str:
    return "safe" if response.power >= 2 + delay else "failed"


def explain_rejection(game: Game, obj: ObjectCfg) -> str:
    return f"(No story: {game.title} does not fit {obj.label} in a way that creates a real little problem.)"


def explain_response(rid: str) -> str:
    return f"(Refusing response '{rid}': it is too weak or too odd for this world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a bouncer, a pot, and peekaboo.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--game", choices=GAMES)
    ap.add_argument("--object", dest="object_cfg", choices=OBJECTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--bouncer-name")
    ap.add_argument("--parent-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--bouncer-gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid in GAMES:
        lines.append(asp.fact("game", gid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("obj", oid))
        if o.risky_if_hidden:
            lines.append(asp.fact("risky_hidden", oid))
        if o.risky_if_play:
            lines.append(asp.fact("risky_play", oid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,G,O) :- setting(S), game(G), obj(O), risky_hidden(O), G = peekaboo.
valid(S,G,O) :- setting(S), game(G), obj(O), risky_play(O), G = hideout.
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
safe(R,D) :- sensible(R), power(R,P), delay(D), P >= D + 2.
"""

def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    m = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(m, "valid")))


def asp_sensible() -> list[str]:
    import asp
    m = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(v for (v,) in asp.atoms(m, "sensible"))


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        rc = 1
        print("MISMATCH in valid combos")
        print("only python:", sorted(py - cl))
        print("only clingo:", sorted(cl - py))
    else:
        print(f"OK: valid combos match ({len(py)}).")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("MISMATCH in sensible responses")
    # smoke test ordinary generation
    try:
        _ = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        print("OK: generate smoke test passed.")
    except Exception as e:  # pragma: no cover
        rc = 1
        print("FAIL: generate smoke test:", e)
    return rc


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError(explain_response(args.response))
    if args.game and args.object_cfg:
        if not reasonableness_gate(GAMES[args.game], OBJECTS[args.object_cfg]):
            raise StoryError(explain_rejection(GAMES[args.game], OBJECTS[args.object_cfg]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.game is None or c[1] == args.game)
              and (args.object_cfg is None or c[2] == args.object_cfg)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, game, obj = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    bouncer_gender = args.bouncer_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    bouncer_name = args.bouncer_name or rng.choice(["Bram", "Bina", "Rook", "Mara", "Hale"])
    parent_name = args.parent_name or rng.choice(["Parent", "Aunt", "Uncle", "Guardian"])
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    return StoryParams(
        setting=setting, game=game, object_cfg=obj, response=response,
        child_name=child_name, child_gender=child_gender,
        bouncer_name=bouncer_name, bouncer_gender=bouncer_gender,
        parent_name=parent_name, seed=None,
    )


def simulate(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS.get(params.setting)
    game = GAMES.get(params.game)
    obj_cfg = OBJECTS.get(params.object_cfg)
    resp = RESPONSES.get(params.response)
    if not setting or not game or not obj_cfg or not resp:
        raise StoryError("Invalid params.")
    if not reasonableness_gate(game, obj_cfg):
        raise StoryError(explain_rejection(game, obj_cfg))
    if resp.sense < 2:
        raise StoryError(explain_response(resp.id))

    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child", meters={"joy": 0.0}, memes={"curiosity": 0.0, "fear": 0.0, "lesson": 0.0}))
    bouncer = world.add(Entity(id=params.bouncer_name, kind="character", type=params.bouncer_gender, role="bouncer", meters={"duty": 1.0}, memes={"care": 0.0, "caution": 0.0}))
    parent = world.add(Entity(id=params.parent_name, kind="character", type="mother", role="parent", meters={"calm": 1.0}, memes={"warmth": 0.0}))
    obj = world.add(Entity(id=obj_cfg.id, kind="thing", type="pot", label=obj_cfg.label, tags=set(obj_cfg.tags), meters={"hidden": 0.0, "wobble": 0.0, "bother": 0.0}))
    world.facts.update(setting=setting, game=game, obj_cfg=obj_cfg, response=resp, child=child, bouncer=bouncer, parent=parent, obj=obj, delay=0 if params.seed is None else params.seed % 3)
    delay = world.facts["delay"]

    world.say(f"At {setting.label}, the air was busy and bright. {setting.scene}.")
    world.say(f'{child.id} peeked at {obj.phrase} and whispered, "{game.title}, right?"')
    world.say(f'{bouncer.id} folded {bouncer.pronoun("possessive")} arms. "Not there," {bouncer.pronoun()} said. "A {obj.label} is for soup, not for hiding."')
    world.para()

    child.memes["curiosity"] += 1
    obj.meters["hidden"] += 1
    world.say(f'{child.id} tried the trick anyway: "{game.title}!" {child.id} cried, and ducked behind the {obj.label}.')
    world.say(f"The {obj.label} gave a hollow little echo. It did not make a good game place.")
    world.para()

    obj.meters["wobble"] += 1
    child.memes["fear"] += 1
    world.say(f'{bouncer.id} stepped close. "If that {obj.label} tips, you will get hurt," {bouncer.id} said. "Come out and play where feet can run."')
    if delay > 1:
        world.say(f'{child.id} bit {child.pronoun("possessive")} lip. The hideout felt less funny now.')
    world.say(f'{child.id} answered, "But I wanted peekaboo."')
    world.para()

    outcome = response_outcome(resp, delay)
    if outcome == "safe":
        child.memes["lesson"] += 1
        child.memes["joy"] += 1
        bouncer.memes["care"] += 1
        world.say(f'{parent.id} came along and said, "{resp.text}."')
        world.say(f'{child.id} climbed out, brushed off {child.pronoun("possessive")} knees, and laughed. "{game.title} can be safe in the yard," {child.id} said.')
        world.say(f"Then {bouncer.id} pointed to a sunny patch by the wall, and the child played peekaboo there instead.")
    else:
        child.memes["fear"] += 2
        world.say(f'{parent.id} came along and said, "{resp.fail}."')
        world.say(f'{bouncer.id} helped steady the {obj.label}, and {child.id} came out quiet and shaken.')
        world.say(f"The fable ended with a small lesson: a game is best when nobody has to risk a tumble.")
    world.facts["outcome"] = outcome
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    bouncer = f["bouncer"]
    parent = f["parent"]
    obj = f["obj"]
    game = f["game"]
    qa = [
        QAItem(
            question=f"What did {child.id} try to do with the {obj.label}?",
            answer=f'{child.id} tried to play {game.title} by hiding in the {obj.label}. That was risky because the {obj.label} was not a safe hiding place.',
        ),
        QAItem(
            question=f'What did {bouncer.id} say about the {obj.label}?',
            answer=f'{bouncer.id} warned that the {obj.label} was for soup, not for hiding. {bouncer.id} wanted {child.id} to play where it would be safe.',
        ),
        QAItem(
            question=f"Who helped finish the lesson in the story?",
            answer=f'{parent.id} came with a calm word, and {bouncer.id} helped steady the {obj.label}. Together they showed {child.id} a safer way to keep playing.',
        ),
    ]
    if f["outcome"] == "safe":
        qa.append(QAItem(
            question=f"How did the story end for {child.id}?",
            answer=f'{child.id} climbed out safely, laughed, and played peekaboo in a better place. The ending proves that a wise choice can keep the game fun.',
        ))
    else:
        qa.append(QAItem(
            question=f"Why was the ending careful and quiet?",
            answer=f'The {obj.label} was wobbly, so everyone chose safety first. The child got out without harm, and the story ends with a lesson instead of a tumble.',
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    obj = world.facts["obj_cfg"]
    game = world.facts["game"]
    out = [
        QAItem("What is peekaboo?", "Peekaboo is a game where someone hides, then pops out so another person can find them. It is meant to be silly and fun."),
        QAItem("What is a bouncer?", "A bouncer is a person who keeps a place safe and orderly. In stories, a bouncer can warn someone before trouble starts."),
    ]
    if obj.id == "pot":
        out.append(QAItem("What is a pot for?", "A pot is a container for cooking or holding things. It is not meant to be climbed into for a game."))
    out.append(QAItem("Why should games be safe?", "Safe games let everyone keep playing without getting hurt. That is the wise choice in a fable."))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    obj = f["obj_cfg"]
    game = f["game"]
    return [
        f'Write a short fable that includes the words "{obj.label}", "{game.title}", and "bouncer".',
        f"Tell a dialogue-heavy story where {child.id} tries to use a {obj.label} for {game.title}, but a bouncer warns them.",
        f"Write a gentle fable about a child, a pot, and peekaboo, ending with a safer choice.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="gate", game="peekaboo", object_cfg="pot", response="lift", child_name="Mina", child_gender="girl", bouncer_name="Bram", bouncer_gender="boy", parent_name="Aunt"),
    StoryParams(setting="market", game="peekaboo", object_cfg="barrel", response="roll", child_name="Oren", child_gender="boy", bouncer_name="Bina", bouncer_gender="girl", parent_name="Uncle"),
]


def valid_story_exists() -> bool:
    return any(reasonableness_gate(GAMES[g], OBJECTS[o]) for _, g, o in valid_combos())


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
