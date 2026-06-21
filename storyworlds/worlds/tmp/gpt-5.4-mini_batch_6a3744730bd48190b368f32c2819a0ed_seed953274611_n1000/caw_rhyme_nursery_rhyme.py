#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/caw_rhyme_nursery_rhyme.py
===========================================================

A tiny nursery-rhyme storyworld about a crow, a lost shiny ring, and a small
helpful turn. The world keeps close to nursery-rhyme style: simple scenes,
gentle tension, a child-facing resolution, and light rhyme in the rendered prose.

The domain premise:
- A crow spots a shiny thing, says "caw," and takes it for a bit.
- A child notices the loss and calls for help.
- A kind helper offers a swap or a safe recovery method.
- The ending proves the change: the shiny thing is back, the crow is content,
  and the child knows what was learned.

This script is standalone and uses only the stdlib plus the repo's shared
results.py container API. ASP is imported lazily only in the ASP helpers.
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
HAPPY_MIN = 2
RHYME_MAX = 3


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
    can_call: bool = False
    can_help: bool = False
    shiny: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    rhythm: str
    rhyme_tail: str
    kind: str = "yard"
    dark_spot: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ShinyThing:
    id: str
    label: str
    phrase: str
    gleam: str
    owner: str
    safe: bool = False
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
    shiny: str
    response: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    crow_name: str
    caw_count: int = 1
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_return(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["taken"] < THRESHOLD:
            continue
        if ent.meters["returned"] >= THRESHOLD:
            continue
        if not ent.attrs.get("belongs_to"):
            continue
        sig = ("return", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["returned"] += 1
        out.append("__return__")
    return out


def _r_smile(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("resolved") and "child" in world.entities:
        child = world.get("child")
        if child.memes["relief"] < THRESHOLD:
            child.memes["relief"] += 1
            out.append("__smile__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("return", "physical", _r_return),
    Rule("smile", "social", _r_smile),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_response(resp: Response) -> bool:
    return resp.sense >= HAPPY_MIN


def caw_risk(shiny: ShinyThing) -> bool:
    return not shiny.safe


def can_restore(response: Response, caw_count: int) -> bool:
    return response.power >= caw_count


def choose_setting(rng: random.Random) -> Setting:
    return SETTINGS[rng.choice(sorted(SETTINGS))]


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(sorted(GIRL_NAMES if gender == "girl" else BOY_NAMES))


def play_intro(world: World, child: Entity, helper: Entity, crow: Entity, setting: Setting) -> None:
    child.memes["wonder"] += 1
    helper.memes["care"] += 1
    crow.memes["curious"] += 1
    world.say(
        f"In {setting.place}, {child.id} went skipping in the light, with a hop and a turn, with a sweet little sight."
    )
    world.say(
        f"There sat {crow.id}, black as night, and when it saw the shine, it gave a bright little caw."
    )


def loss(world: World, child: Entity, crow: Entity, shiny: ShinyThing, setting: Setting, caw_count: int) -> None:
    crow.meters["taken"] += 1
    crow.meters["gleam"] += 1
    crow.memes["glee"] += 1
    world.say(
        f"{crow.id} said {'caw ' * max(1, caw_count)}and flew to the bough, with {shiny.phrase} held in its beak."
    )
    world.say(
        f"Then {child.id} looked near the nest and looked by the wall, but the shiny thing was gone from the small garden hall."
    )
    child.memes["sad"] += 1


def warn(world: World, child: Entity, helper: Entity, shiny: ShinyThing, crow: Entity) -> None:
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} said, \"No fuss, little one; call kindly and slow. A crow may be clever, but kindness can show.\""
    )
    world.say(
        f"{child.id} bit {child.pronoun('possessive')} lip and called, \"Hello, black crow, please bring it back home.\""
    )


def predict_return(world: World, response: Response, caw_count: int) -> bool:
    return can_restore(response, caw_count)


def resolve(world: World, helper: Entity, child: Entity, crow: Entity, shiny: ShinyThing, response: Response) -> None:
    if response.id == "bread":
        world.say(
            f"{helper.id} held up a crusty crumb and sang, \"Swap for a snack, and the shiny comes back.\""
        )
        crow.memes["interested"] += 1
    elif response.id == "bell":
        world.say(
            f"{helper.id} rang a tiny bell, ding-ding in the air, and the sound made the crow stare and stare."
        )
        crow.memes["curious"] += 1
    else:
        world.say(
            f"{helper.id} kept a calm voice and a gentle pace, and the crow came gliding back to the place."
        )
    if response.power >= 1:
        crow.meters["returned"] += 1
        shiny.safe = True
        world.say(
            f"{crow.id} dipped and swooped, then dropped {shiny.phrase} near {child.id}'s feet, all bright and neat."
        )
        world.say(response.text.replace("{shiny}", shiny.label))
        child.memes["joy"] += 1
        helper.memes["joy"] += 1
    else:
        world.say(response.fail.replace("{shiny}", shiny.label))


def ending(world: World, child: Entity, helper: Entity, crow: Entity, shiny: ShinyThing, setting: Setting) -> None:
    world.say(
        f"Now {child.id} has {shiny.phrase} once more, and {crow.id} has a crumb and a high branch to explore."
    )
    world.say(
        f"In {setting.place}, the day ends light, with a caw and a smile and a soft, happy flight."
    )
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    crow.memes["content"] += 1


def tell(setting: Setting, shiny: ShinyThing, response: Response, child_name: str, child_gender: str,
         helper_name: str, helper_gender: str, crow_name: str, caw_count: int) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", can_help=True))
    crow = world.add(Entity(id=crow_name, kind="character", type="crow", role="crow"))
    item = world.add(Entity(id="shiny", type="thing", label=shiny.label, shiny=True, attrs={"belongs_to": child.id}))
    world.facts["shiny_cfg"] = shiny
    world.facts["response"] = response
    world.facts["crow"] = crow
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["item"] = item
    world.facts["caw_count"] = caw_count
    play_intro(world, child, helper, crow, setting)
    world.para()
    loss(world, child, crow, shiny, setting, caw_count)
    warn(world, child, helper, shiny, crow)
    world.para()
    if predict_return(world, response, caw_count):
        resolve(world, helper, child, crow, shiny, response)
        world.facts["resolved"] = True
    else:
        world.say(
            f"The helper tried, but the plan was too small and the crow flew high and free."
        )
        world.say(
            f"So {child.id} waved goodbye, and the shiny thing stayed in the tree."
        )
        world.facts["resolved"] = False
    world.para()
    ending(world, child, helper, crow, shiny, setting)
    return world


SETTINGS = {
    "yard": Setting(id="yard", place="the yard", rhythm="hop and bound", rhyme_tail="light and bright", kind="yard", dark_spot="the hedge", tags={"yard"}),
    "pond": Setting(id="pond", place="the pond", rhythm="skip and spin", rhyme_tail="glad again", kind="pond", dark_spot="the reeds", tags={"pond"}),
    "lane": Setting(id="lane", place="the lane", rhythm="tap and clap", rhyme_tail="back again", kind="lane", dark_spot="the fence", tags={"lane"}),
}

SHINY_THINGS = {
    "ring": ShinyThing(id="ring", label="a silver ring", phrase="the silver ring", gleam="gleamed", owner="child", safe=False, tags={"shiny"}),
    "button": ShinyThing(id="button", label="a bright button", phrase="the bright button", gleam="blinked", owner="child", safe=False, tags={"shiny"}),
    "pin": ShinyThing(id="pin", label="a tiny pin", phrase="the tiny pin", gleam="twinkled", owner="child", safe=False, tags={"shiny"}),
}

RESPONSES = {
    "bread": Response(id="bread", sense=3, power=1, text="The crow took the bread and brought back {shiny}.", fail="The bread was too small, and the crow kept {shiny}.", tags={"swap"}),
    "bell": Response(id="bell", sense=2, power=1, text="The bell rang soft and clear, and back came {shiny} near.", fail="The bell rang, but the crow only hopped and kept {shiny}.", tags={"sound"}),
    "call": Response(id="call", sense=3, power=1, text="The crow heard the kind call and came back with {shiny} in tow.", fail="The crow heard the call, but the wind pushed it away from {shiny}.", tags={"call"}),
}

GIRL_NAMES = ["Lily", "Mia", "Nora", "Ava", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Finn", "Leo", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for shiny_id, shiny in SHINY_THINGS.items():
            if not caw_risk(shiny):
                continue
            for rid, resp in RESPONSES.items():
                if valid_response(resp):
                    combos.append((sid, shiny_id, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about a cawing crow and a returned shiny thing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--shiny", choices=SHINY_THINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["mother", "father", "girl", "boy"])
    ap.add_argument("--crow-name")
    ap.add_argument("--caw-count", type=int, choices=[1, 2, 3], help="How many caws the crow makes.")
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
    if args.response and not valid_response(RESPONSES[args.response]):
        raise StoryError("(No story: that response is too weak for this little rhyme.)")
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.shiny is None or c[1] == args.shiny)
        and (args.response is None or c[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, shiny, response = rng.choice(sorted(combos))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting,
        shiny=shiny,
        response=response,
        child_name=args.child_name or choose_name(rng, gender),
        child_gender=gender,
        helper_name=args.helper_name or choose_name(rng, "girl" if helper_gender == "mother" else "boy"),
        helper_gender=helper_gender,
        crow_name=args.crow_name or rng.choice(["Crow", "Corbie", "Blackie"]),
        caw_count=args.caw_count if args.caw_count is not None else rng.randint(1, 3),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme story that includes the word "caw" and ends with a gentle rhyme.',
        f"Tell a child-friendly rhyme where {f['crow'].id} takes {f['item'].label} for a bit and a helper gets it back.",
        f"Write a small story about a crow, a shiny thing, and a kind answer that makes the shiny come home.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, crow, shiny = f["child"], f["helper"], f["crow"], f["item"]
    response = f["response"]
    items = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {child.id}, {helper.id}, and {crow.id}, with {shiny.label} at the center of the little rhyme. The crow's cawing starts the problem, and the helper helps bring the shiny thing back.",
        ),
        QAItem(
            question=f"What happened when {crow.id} saw the shiny thing?",
            answer=f"{crow.id} took {shiny.label} and flew off with a bright caw. That made {child.id} sad, because the shiny thing belonged to {child.id}.",
        ),
    ]
    if f.get("resolved"):
        items.append(
            QAItem(
                question=f"How did they get {shiny.label} back?",
                answer=f"{helper.id} stayed calm and used a gentle {response.id}-style answer, and the crow brought {shiny.label} back. The safe choice worked because it matched the little problem and did not frighten the bird away.",
            )
        )
        items.append(
            QAItem(
                question=f"How did the story end?",
                answer=f"It ended with {child.id} smiling, {crow.id} content, and {shiny.label} back where it belonged. The last image is a quiet one: a caw, a smile, and a shiny thing in the hand again.",
            )
        )
    else:
        items.append(
            QAItem(
                question=f"Why didn't the shiny thing come back right away?",
                answer=f"The helper tried to fix it, but the chosen answer was too small for the crow's high flight. So the shiny thing stayed away for a while, and the story ended with waiting instead of a return.",
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a crow say?",
            answer="A crow often says caw. It is a loud bird sound, and it can sound sharp and clear in a little rhyme.",
        ),
        QAItem(
            question="What is a shiny thing?",
            answer="A shiny thing is something that catches the light and gleams or twinkles. Children notice shiny things quickly because they sparkle and stand out.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="yard", shiny="ring", response="bread", child_name="Lily", child_gender="girl", helper_name="Mum", helper_gender="mother", crow_name="Crow", caw_count=1),
    StoryParams(setting="pond", shiny="button", response="bell", child_name="Tom", child_gender="boy", helper_name="Dad", helper_gender="father", crow_name="Corbie", caw_count=2),
    StoryParams(setting="lane", shiny="pin", response="call", child_name="Nora", child_gender="girl", helper_name="Mia", helper_gender="girl", crow_name="Blackie", caw_count=3),
]


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': sense={r.sense} is too low for this gentle nursery rhyme.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid, s.place))
    for sid in SHINY_THINGS:
        lines.append(asp.fact("shiny", sid))
    for sid, sh in SHINY_THINGS.items():
        if not sh.safe:
            lines.append(asp.fact("risk", sid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", HAPPY_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, X, R) :- setting(S), shiny(X), risk(X), response(R), sense(R, V), sense_min(M), V >= M.
resolved(R) :- response(R), power(R, P), need(N), P >= N.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp as _asp
    ok = set(asp_valid_combos()) == set(valid_combos())
    rc = 0 if ok else 1
    if ok:
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH between clingo and valid_combos().")
        rc = 1
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("MISMATCH: story generation produced empty text.")
        rc = 1
    print("OK: normal story generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("unknown setting")
    if params.shiny not in SHINY_THINGS:
        raise StoryError("unknown shiny thing")
    if params.response not in RESPONSES:
        raise StoryError("unknown response")
    if params.caw_count < 1:
        raise StoryError("caw_count must be positive")
    response = RESPONSES[params.response]
    if not valid_response(response):
        raise StoryError(explain_response(params.response))
    setting = SETTINGS[params.setting]
    shiny = SHINY_THINGS[params.shiny]
    world = tell(setting, shiny, response, params.child_name, params.child_gender,
                 params.helper_name, params.helper_gender, params.crow_name, params.caw_count)
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


def resolve_combos(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.shiny is None or c[1] == args.shiny)
        and (args.response is None or c[2] == args.response)
    ]
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and not valid_response(RESPONSES[args.response]):
        raise StoryError(explain_response(args.response))
    combos = resolve_combos(args)
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, shiny, response = rng.choice(sorted(combos))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting,
        shiny=shiny,
        response=response,
        child_name=args.child_name or choose_name(rng, gender),
        child_gender=gender,
        helper_name=args.helper_name or choose_name(rng, "girl" if helper_gender == "mother" else "boy"),
        helper_gender=helper_gender,
        crow_name=args.crow_name or rng.choice(["Crow", "Corbie", "Blackie"]),
        caw_count=args.caw_count if args.caw_count is not None else rng.randint(1, 3),
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld with a cawing crow.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--shiny", choices=SHINY_THINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["mother", "father", "girl", "boy"])
    ap.add_argument("--crow-name")
    ap.add_argument("--caw-count", type=int, choices=[1, 2, 3])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (setting, shiny, response) combos:")
        for s, x, r in asp_valid_combos():
            print(f"  {s:6} {x:8} {r}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
