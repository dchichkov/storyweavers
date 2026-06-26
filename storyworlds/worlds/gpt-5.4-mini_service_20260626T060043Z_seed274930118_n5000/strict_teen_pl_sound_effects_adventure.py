#!/usr/bin/env python3
"""
storyworlds/worlds/strict_teen_pl_sound_effects_adventure.py
============================================================

A small adventure storyworld about a strict rulebook, a teen-pl trail, and
sound effects that help a child solve a little quest.

Premise:
- A young explorer wants to cross a tricky place on the teen-pl route.
- A strict guide worries about noise, echoes, and a fragile goal item.
- The explorer must listen closely, use the right sound effects, and solve the
  problem without making a mess.

This world keeps the adventure feel close to classic quest stories:
- beginning: the child sets out with a goal
- middle: a warning, a mistaken choice, and a tense turn
- end: a smarter sound-based fix proves what changed

The world model uses meters for physical state and memes for emotional state.
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self):
        for k in ["noise", "echo", "dust", "damage", "distance"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "fear", "focus", "annoyance", "pride", "strictness"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the teen-pl trail"
    indoor: bool = False
    echo_level: float = 1.0
    strictness: float = 1.0
    affords: set[str] = field(default_factory=set)


@dataclass
class SoundAction:
    id: str
    sound: str
    sound_effect: str
    danger: str
    echo: float
    noise: float
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GoalItem:
    label: str
    phrase: str
    type: str
    breakable: bool = True
    needs_quiet: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: set[str]
    guards_noise: bool = False
    guards_echo: bool = False
    prep: str = ""
    tail: str = ""
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.route: str = ""
        self.sound_mode: str = ""

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.route = self.route
        clone.sound_mode = self.sound_mode
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_noise(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["noise"] < THRESHOLD:
            continue
        sig = ("noise", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["annoyance"] += 1
        if world.setting.echo_level > 0.5:
            actor.meters["echo"] += 1
            out.append(f"The sound bounced back off the walls.")
        else:
            out.append(f"The sound stayed small and close.")
    return out


def _r_break(world: World) -> list[str]:
    out = []
    goal = world.entities.get("goal")
    if not goal:
        return out
    for actor in world.characters():
        if actor.meters["noise"] < THRESHOLD:
            continue
        sig = ("break", actor.id)
        if sig in world.fired:
            continue
        if goal.meters["damage"] >= THRESHOLD:
            continue
        if world.setting.strictness > 0.5 and goal.needs_quiet:
            world.fired.add(sig)
            goal.meters["damage"] += 1
            out.append("The fragile goal item cracked a little.")
    return out


def _r_calm(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes["focus"] < THRESHOLD:
            continue
        sig = ("calm", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["noise"] = max(0.0, actor.meters["noise"] - 1.0)
        actor.memes["joy"] += 1
        out.append("The explorer listened carefully and got calmer.")
    return out


RULES = [
    _r_noise,
    _r_break,
    _r_calm,
]


def propagate(world: World) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            s = rule(world)
            if s:
                changed = True
                out.extend(s)
    for line in out:
        world.say(line)
    return out


def predict_break(world: World, actor: Entity, action: SoundAction) -> bool:
    sim = world.copy()
    sim.get(actor.id).meters["noise"] += action.noise
    propagate(sim)
    goal = sim.entities["goal"]
    return goal.meters["damage"] >= THRESHOLD


def sound_effect_line(action: SoundAction) -> str:
    return f"{action.sound_effect}!"


def safe_tool_for(action: SoundAction, goal: GoalItem) -> Optional[Tool]:
    for tool in TOOLS:
        if action.id in tool.helps_with and (not goal.needs_quiet or tool.guards_noise or tool.guards_echo):
            return tool
    return None


def tell(setting: Setting, action: SoundAction, goal_cfg: GoalItem, hero_name: str, hero_type: str, guide_type: str) -> World:
    world = World(setting)
    world.route = setting.place
    world.sound_mode = action.id

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["bold", "curious"]))
    guide = world.add(Entity(id="Guide", kind="character", type=guide_type, label="the strict guide"))
    goal = world.add(Entity(
        id="goal",
        type=goal_cfg.type,
        label=goal_cfg.label,
        phrase=goal_cfg.phrase,
        owner=hero.id,
        caretaker=guide.id,
        plural=False,
    ))
    goal.needs_quiet = goal_cfg.needs_quiet

    world.say(f"{hero.id} was a bold little explorer who loved a good adventure.")
    world.say(f"{hero.pronoun().capitalize()} had come to {setting.place} with a clear goal: {goal_cfg.phrase}.")
    world.say(f"At the trailhead, {guide.label} pointed to a sign that said strict rules only.")
    world.say(f'"Listen first," {guide.pronoun("subject")} said. "On the teen-pl trail, even small sounds can matter."')

    world.para()
    world.say(f"{hero.id} wanted to keep going, so {hero.pronoun()} tested the path.")
    hero.meters["noise"] += action.noise
    hero.meters["distance"] += 1
    world.say(sound_effect_line(action))
    if predict_break(world, hero, action):
        world.say(f"But the {action.danger} made {goal.label} shake.")
        guide.memes["strictness"] += 1
        hero.memes["fear"] += 1
        world.say(f'{guide.label} lifted a hand and said, "Too loud."')
        world.say(f"{hero.id} stopped fast and looked at {goal.label}.")
    propagate(world)

    world.para()
    tool = safe_tool_for(action, goal_cfg)
    if tool is None:
        world.say(f"{hero.id} listened harder and found a quieter way by using {action.clue}.")
        hero.memes["focus"] += 1
        propagate(world)
        world.say(f"The path opened a little, and {goal.label} stayed safe.")
    else:
        world.say(f'{guide.label} nodded and showed {hero.id} {tool.phrase}.')
        world.say(f'"Try this first," {guide.pronoun("subject")} said. "{tool.prep}."')
        hero.memes["focus"] += 1
        if tool.guards_noise:
            hero.meters["noise"] = max(0.0, hero.meters["noise"] - 1.0)
        if tool.guards_echo:
            hero.meters["echo"] = max(0.0, hero.meters["echo"] - 1.0)
        world.say(f"{hero.id} used it and the sounds turned neat and small.")
        if action.id == "whistle":
            world.say("Pee-pip!")
        elif action.id == "tap":
            world.say("Tick-tick!")
        else:
            world.say("Tap-tap!")
        world.say(f"That was quiet enough for {goal.label}.")
        hero.memes["joy"] += 1
        guide.memes["strictness"] -= 0.5
        propagate(world)

    world.say(f"In the end, {hero.id} reached the goal and {goal.label} stayed whole.")
    world.say(f"The teen-pl trail felt less scary, and the strict sign felt more like a helpful warning than a wall.")

    world.facts.update(
        hero=hero,
        guide=guide,
        goal=goal,
        goal_cfg=goal_cfg,
        action=action,
        setting=setting,
        tool=tool,
    )
    return world


SETTINGS = {
    "trail": Setting(place="the teen-pl trail", indoor=False, echo_level=0.8, strictness=1.0, affords={"whistle", "tap", "snap"}),
    "cave": Setting(place="the teen-pl cave", indoor=True, echo_level=1.0, strictness=1.2, affords={"whistle", "tap", "snap"}),
    "bridge": Setting(place="the teen-pl bridge", indoor=False, echo_level=0.6, strictness=0.9, affords={"whistle", "tap", "snap"}),
}

ACTIONS = {
    "whistle": SoundAction(
        id="whistle",
        sound="a high whistle",
        sound_effect="fwee-fwee",
        danger="sharp echo",
        echo=1.0,
        noise=1.0,
        clue="a hand sign and a slow breath",
        tags={"sound", "echo"},
    ),
    "tap": SoundAction(
        id="tap",
        sound="a tiny tap",
        sound_effect="tap-tap",
        danger="hard thump",
        echo=0.3,
        noise=0.7,
        clue="a soft toe-step",
        tags={"sound", "quiet"},
    ),
    "snap": SoundAction(
        id="snap",
        sound="a finger snap",
        sound_effect="snap",
        danger="snappy burst",
        echo=0.6,
        noise=0.8,
        clue="rubbing fingers together first",
        tags={"sound", "sharp"},
    ),
}

GOALS = {
    "bell": GoalItem(
        label="bronze bell",
        phrase="find the bronze bell at the end of the trail",
        type="bell",
        breakable=True,
        needs_quiet=True,
        genders={"girl", "boy"},
    ),
    "map": GoalItem(
        label="paper map",
        phrase="carry the paper map through the route without tearing it",
        type="map",
        breakable=True,
        needs_quiet=False,
        genders={"girl", "boy"},
    ),
    "lantern": GoalItem(
        label="glass lantern",
        phrase="bring the glass lantern to the lookout without cracking it",
        type="lantern",
        breakable=True,
        needs_quiet=True,
        genders={"girl", "boy"},
    ),
}

TOOLS = [
    Tool(
        id="hood",
        label="a padded hood",
        phrase="a padded hood",
        helps_with={"whistle", "snap"},
        guards_noise=True,
        guards_echo=False,
        prep="put it on and keep the sound tucked in",
        tail="pulled the hood low and kept the noise small",
    ),
    Tool(
        id="cloth",
        label="a soft cloth",
        phrase="a soft cloth to wrap the bell",
        helps_with={"tap", "whistle", "snap"},
        guards_noise=True,
        guards_echo=True,
        prep="wrap the item before moving it",
        tail="wrapped the goal item and carried it gently",
    ),
    Tool(
        id="gloves",
        label="padded gloves",
        phrase="padded gloves",
        helps_with={"tap", "snap"},
        guards_noise=True,
        guards_echo=False,
        prep="wear them and keep every touch light",
        tail="moved with careful little hands",
    ),
]

HERO_NAMES = ["Mila", "Noa", "Theo", "Iris", "Jules", "Arin", "Pia", "Luca"]
HERO_TYPES = ["girl", "boy"]
GUIDE_TYPES = ["father", "mother", "guide", "uncle"]
TRAITS = ["careful", "curious", "brave", "strict"]


@dataclass
class StoryParams:
    place: str
    action: str
    goal: str
    name: str
    hero_type: str
    guide_type: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for action_id in setting.affords:
            action = ACTIONS[action_id]
            for goal_id, goal in GOALS.items():
                if goal.needs_quiet and safe_tool_for(action, goal) is None:
                    continue
                combos.append((place, action_id, goal_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a child who hears "{f["action"].sound_effect}" on the teen-pl trail.',
        f"Tell a strict-but-kind story where {f['hero'].id} must protect {f['goal'].label} from sound.",
        f'Write a short adventure with a clear sound effect and a quiet solution at {f["setting"].place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    goal = f["goal"]
    action = f["action"]
    tool = f["tool"]
    qs = [
        QAItem(
            question=f"What did {hero.id} want to do on the teen-pl trail?",
            answer=f"{hero.id} wanted to keep going on the teen-pl trail and use {action.sound}.",
        ),
        QAItem(
            question=f"Why was {guide.label} strict about the sound?",
            answer=f"{guide.label} was strict because loud sound could make the {goal.label} shake or crack.",
        ),
        QAItem(
            question=f"What did the sound effect say when {hero.id} tried the path?",
            answer=f"The sound effect was {action.sound_effect}, which matched the first noisy try.",
        ),
    ]
    if tool:
        qs.append(QAItem(
            question=f"How did {tool.label} help {hero.id} finish the adventure?",
            answer=f"{tool.label} helped by keeping the sound smaller and safer, so {goal.label} stayed whole.",
        ))
    return qs


WORLD_KNOWLEDGE = {
    "sound": [
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a made-up or special sound that helps a story feel lively, like tap-tap or fwee-fwee.",
        )
    ],
    "echo": [
        QAItem(
            question="What is an echo?",
            answer="An echo is a sound that bounces back after it hits a wall, a cave, or another hard surface.",
        )
    ],
    "quiet": [
        QAItem(
            question="Why do some places need quiet?",
            answer="Some places need quiet because loud sounds can scare animals, bother people, or break something fragile.",
        )
    ],
    "trail": [
        QAItem(
            question="What is a trail?",
            answer="A trail is a path you can follow outdoors when you go exploring or hiking.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = set(world.facts["action"].tags)
    if world.facts["goal"].needs_quiet:
        tags.add("quiet")
    if world.setting.echo_level > 0.5:
        tags.add("echo")
    tags.add("trail")
    for key in ["sound", "echo", "quiet", "trail"]:
        if key in tags:
            out.extend(WORLD_KNOWLEDGE[key])
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = []
    for title, items in [
        ("== prompts ==", sample.prompts),
        ("== story qa ==", sample.story_qa),
        ("== world qa ==", sample.world_qa),
    ]:
        lines.append(title)
        if title == "== prompts ==":
            for i, p in enumerate(items, 1):
                lines.append(f"{i}. {p}")
        else:
            for item in items:
                lines.append(f"Q: {item.question}")
                lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("noise", aid, int(a.noise * 10)))
        lines.append(asp.fact("echo", aid, int(a.echo * 10)))
    for gid, g in GOALS.items():
        lines.append(asp.fact("goal", gid))
        if g.needs_quiet:
            lines.append(asp.fact("needs_quiet", gid))
    for tid, t in enumerate(TOOLS):
        lines.append(asp.fact("tool", t.id))
        for a in sorted(t.helps_with):
            lines.append(asp.fact("helps", t.id, a))
        if t.guards_noise:
            lines.append(asp.fact("guards_noise", t.id))
        if t.guards_echo:
            lines.append(asp.fact("guards_echo", t.id))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, A, G) :- affords(Place, A), action(A), goal(G), not blocked(A, G).
blocked(A, G) :- needs_quiet(G), not fix(A, G).
fix(A, G) :- tool(T), helps(T, A), (guards_noise(T); guards_echo(T)).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with sound effects and a strict guide.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--guide", choices=["mother", "father", "guide", "uncle"])
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
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.action is None or c[1] == args.action)
        and (args.goal is None or c[2] == args.goal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, goal = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(HERO_TYPES)
    name = args.name or rng.choice(HERO_NAMES)
    guide_type = args.guide or rng.choice(GUIDE_TYPES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, action=action, goal=goal, name=name, hero_type=gender, guide_type=guide_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], GOALS[params.goal], params.name, params.hero_type, params.guide_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="trail", action="whistle", goal="bell", name="Mila", hero_type="girl", guide_type="mother", trait="curious"),
    StoryParams(place="cave", action="tap", goal="lantern", name="Theo", hero_type="boy", guide_type="father", trait="brave"),
    StoryParams(place="bridge", action="snap", goal="map", name="Iris", hero_type="girl", guide_type="guide", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
            header = f"### {p.name}: {p.action} at {p.place} (goal: {p.goal})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
