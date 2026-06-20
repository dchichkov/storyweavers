#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bannister_friend_s_backyard_twist_teamwork_curiosity.py
======================================================================================

A standalone story world for a small animal tale in a friend's backyard: a
curious animal notices something twisty near a bannister-like playrail, teamwork
helps solve the problem, and the ending proves the team has changed the yard for
the better.

This world keeps the "animal story" feel: small characters, concrete objects,
simple cause and effect, and an ending image that shows teamwork and curiosity
paying off.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/bannister_friend_s_backyard_twist_teamwork_curiosity.py
    python storyworlds/worlds/gpt-5.4-mini/bannister_friend_s_backyard_twist_teamwork_curiosity.py --all
    python storyworlds/worlds/gpt-5.4-mini/bannister_friend_s_backyard_twist_teamwork_curiosity.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/bannister_friend_s_backyard_twist_teamwork_curiosity.py --trace --qa
    python storyworlds/worlds/gpt-5.4-mini/bannister_friend_s_backyard_twist_teamwork_curiosity.py --json
    python storyworlds/worlds/gpt-5.4-mini/bannister_friend_s_backyard_twist_teamwork_curiosity.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    place: str
    backdrop: str
    twisty_item: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Action:
    id: str
    verb: str
    effect: str
    zone: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    region: str
    twisty: bool = False
    can_snag: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.objects: dict[str, ObjectThing] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_object(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.id] = obj
        return obj

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.objects = copy.deepcopy(self.objects)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    for obj in world.objects.values():
        if obj.meters["twisted"] < THRESHOLD:
            continue
        sig = ("twist", obj.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ent in list(world.entities.values()):
            if ent.role in {"curious", "helper"}:
                ent.memes["attention"] += 1
        out.append("__twist__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("problem_solved"):
        return out
    helpers = [e for e in list(world.entities.values()) if e.role in {"curious", "helper"}]
    if len(helpers) >= 2 and world.facts.get("ready_to_fix"):
        sig = ("teamwork",)
        if sig not in world.fired:
            world.fired.add(sig)
            for e in helpers:
                e.memes["joy"] += 1
                e.memes["team"] += 1
            out.append("__teamwork__")
    return out


CAUSAL_RULES = [_r_twist, _r_teamwork]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for aid, action in ACTIONS.items():
            for oid, obj in OBJECTS.items():
                if action.zone == obj.region and obj.can_snag:
                    combos.append((sid, aid, oid))
    return combos


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def story_can_happen(setting: Setting, action: Action, obj: ObjectThing) -> bool:
    return action.zone == obj.region and obj.can_snag


def outcome_of(params: "StoryParams") -> str:
    return "fixed" if RESPONSE_POWER[params.response] >= 1 else "stuck"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("zone", aid, a.zone))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("region", oid, o.region))
        if o.can_snag:
            lines.append(asp.fact("can_snag", oid))
        if o.twisty:
            lines.append(asp.fact("twisty", oid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, A, O) :- setting(S), action(A), object(O), zone(A, R), region(O, R), can_snag(O).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: valid combos match ({len(py)}).")
    else:
        rc = 1
        print("MISMATCH in valid combos")
    ps = {r.id for r in sensible_responses()}
    cs = set(asp_sensible())
    if ps == cs:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        assert sample.story.strip()
        print("OK: smoke test story generation works.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story about curiosity, teamwork, and a twisty backyard problem.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=NAMES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    setting_id = args.setting or rng.choice(list(SETTINGS))
    action_id = args.action or rng.choice(list(ACTIONS))
    object_id = args.object_ or rng.choice(list(OBJECTS))
    setting = SETTINGS[setting_id]
    action = ACTIONS[action_id]
    obj = OBJECTS[object_id]
    if not story_can_happen(setting, action, obj):
        raise StoryError("The twisty backyard problem does not fit this action and object.")
    response = args.response or rng.choice([r.id for r in sensible_responses()])
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != name])
    return StoryParams(setting_id, action_id, object_id, response, name, helper, seed=args.seed)


@dataclass
@dataclass
class StoryParams:
    setting: str
    action: str
    object_: str
    response: str
    name: str
    helper: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    action = ACTIONS[params.action]
    obj = OBJECTS[params.object_]
    world = World(setting)
    hero = world.add(Entity(params.name, kind="character", type="animal", role="curious"))
    helper = world.add(Entity(params.helper, kind="character", type="animal", role="helper"))
    world.add(Entity("Parent", kind="character", type="adult", label="the grown-up", role="adult"))
    world.add_object(copy.deepcopy(obj))

    hero.memes["curiosity"] += 1
    helper.memes["team"] += 1

    world.say(
        f"In {setting.place}, {hero.id} the little animal noticed a twisty thing near the bannister."
        f" The {setting.backdrop} made the yard feel like a place for questions."
    )
    world.say(
        f"{hero.id} tilted {hero.pronoun('possessive')} head and peered closer. "
        f'"What is that little twist?" {hero.pronoun()} asked.'
    )
    world.para()
    world.say(
        f"{helper.id} trotted over fast, and together they saw that the {obj.label} had hooked itself on the playrail."
    )
    obj.meters["twisted"] += 1
    world.facts["ready_to_fix"] = True
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} used curious eyes, {helper.id} used quick paws, and the two animals worked side by side."
    )
    response = RESPONSES[params.response]
    if response.power >= 1:
        world.facts["problem_solved"] = True
        obj.meters["twisted"] = 0
        for e in (hero, helper):
            e.memes["joy"] += 1
        world.say(
            f"They gently untwisted the {obj.label}, and the little snag came free at last."
        )
        world.say(
            f"{hero.id} and {helper.id} looked at the clear bannister again and grinned. "
            f"The backyard was calm, and curiosity had helped them fix what they found."
        )
    else:
        world.say("They tried, but the twist stayed stuck.")
    world.facts.update(setting=setting, action=action, object=obj, hero=hero, helper=helper, response=response)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story set in a friend\'s backyard that includes the word "bannister" and shows curiosity leading to teamwork.',
        f"Tell a short story where {f['hero'].id} notices a twist near the bannister, asks a question, and works with {f['helper'].id} to fix it.",
        "Write a gentle backyard animal story with a twisty problem, teamwork, and a calm ending image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    obj = f["object"]
    setting = f["setting"]
    qa = [
        ("Where does the story happen?",
         f"It happens in {setting.place}, in a friend's backyard. That is where the animals notice the twisty problem near the bannister."),
        ("What did the curious animal notice?",
         f"{hero.id} noticed a twisty snag near the bannister. Curiosity made {hero.pronoun()} stop and look instead of rushing past."),
        ("How did they fix the problem?",
         f"{hero.id} and {helper.id} worked together and gently untwisted the {obj.label}. Teamwork let them solve it without making a fuss."),
        ("How did the story end?",
         f"It ended with the bannister clear and the backyard calm. The animals had turned curiosity into teamwork, so the little snag was gone."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is curiosity?",
         "Curiosity is wanting to know more about something. It helps animals and children stop, look, and ask questions."),
        ("What is teamwork?",
         "Teamwork means working together to do a job. Each helper does a part, and the group can solve a problem faster."),
        ("What is a twist?",
         "A twist is a bend or turn. Something twisty can hook, turn, or get tangled up."),
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    for o in world.objects.values():
        bits = []
        meters = {k: v for k, v in o.meters.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if o.tags:
            bits.append(f"tags={sorted(o.tags)}")
        lines.append(f"  {o.id:10} (object ) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {
    "friends_backyard": Setting("a friend's backyard", "a swinging tree branch and a little garden gate", "bannister"),
}
ACTIONS = {
    "twist": Action("twist", "twist", "a twist", "rail", {"curiosity", "twist"}),
}
OBJECTS = {
    "rope": ObjectThing("rope", "rope", "a thin rope", "rail", twisty=True, can_snag=True, tags={"twist"}),
    "vine": ObjectThing("vine", "vine", "a green vine", "rail", twisty=True, can_snag=True, tags={"twist"}),
}
RESPONSES = {
    "untwist": Response("untwist", 3, 3, "untwisted the snag with gentle paws", "tried to pull it free, but it stayed stuck", "gently untwisted the snag"),
    "call_help": Response("call_help", 2, 1, "called for help and pointed out the snag", "called for help, but nobody came in time", "called for help"),
    "ignore": Response("ignore", 1, 0, "looked away and left it there", "ignored it, and the snag stayed", "ignored it"),
}
RESPONSE_POWER = {k: v.power for k, v in RESPONSES.items()}
NAMES = ["Milo", "Nina", "Pip", "Luna", "Otis", "Bibi"]


CURATED = [
    StoryParams("friends_backyard", "twist", "rope", "untwist", "Milo", "Nina"),
    StoryParams("friends_backyard", "twist", "vine", "untwist", "Luna", "Otis"),
]


def asp_verify_story(world: World) -> None:
    if not world.render().strip():
        raise StoryError("Story generation produced empty text.")


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    asp_verify_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for combo in asp_valid_combos():
            print(" ".join(map(str, combo)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
