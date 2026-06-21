#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lumber_happy_ending_tall_tale.py
=================================================================

A standalone story world for a tall-tale style lumber adventure with a happy
ending. It models a small sawmill-and-river domain where a boastful helper and a
careful helper try to move a heavy lumber load before a storm, discover that the
logs have slipped into a jam, and then solve the problem together with a clever,
safe plan.

The generated stories stay close to a Tall Tale tone: larger-than-life images,
simple cause and effect, and a bright ending that proves what changed.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
JAM_MIN = 2.0


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
class Place:
    id: str
    label: str
    water: bool = False
    windy: bool = False
    steep: bool = False


@dataclass
class Load:
    id: str
    label: str
    phrase: str
    heavy: bool = True
    floating: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wind(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["load"] < THRESHOLD:
            continue
        sig = ("wind", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "river" in world.entities and world.get("river").attrs.get("storm", False):
            world.get("river").meters["jam"] += 1
        out.append("")
    return out


def _r_river(world: World) -> list[str]:
    out: list[str] = []
    if "river" not in world.entities:
        return out
    river = world.get("river")
    if river.meters["jam"] < JAM_MIN:
        return out
    sig = ("jam_scary",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in world.entities.values():
        if e.role in {"hauler", "watcher"}:
            e.memes["worry"] += 1
    out.append("")
    return out


CAUSAL_RULES = [
    Rule("wind", "physical", _r_wind),
    Rule("river", "physical", _r_river),
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
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def load_at_risk(place: Place, load: Load) -> bool:
    return place.water and load.heavy


def valid_plan(plan: Plan) -> bool:
    return plan.sense >= 2


def jam_severity(place: Place, delay: int) -> int:
    base = 2 if place.water else 1
    return base + delay


def plan_works(plan: Plan, place: Place, delay: int) -> bool:
    return plan.power >= jam_severity(place, delay)


def predict_jam(world: World, load_id: str) -> dict:
    sim = world.copy()
    sim.get(load_id).meters["load"] += 1
    propagate(sim, narrate=False)
    return {"jam": sim.get("river").meters["jam"] if "river" in sim.entities else 0}


def _move_load(world: World, load: Entity) -> None:
    load.meters["load"] += 1
    propagate(world, narrate=False)


def start(world: World, hero: Entity, helper: Entity, place: Place, load: Load) -> None:
    hero.memes["moxie"] += 1
    helper.memes["care"] += 1
    world.say(
        f"In the days when {place.label} sat under the sky like a great blue hat, "
        f"{hero.id} and {helper.id} came to the bank to haul a load of lumber."
    )
    world.say(
        f"The lumber was stacked high as a barn door and broad as a cornstalk field, "
        f"waiting for a brave pair of hands."
    )


def trouble(world: World, hero: Entity, helper: Entity, place: Place, load: Load) -> None:
    world.say(
        f"But the river beside {place.label} had a dark twist in it, and the wind "
        f"gave the logs a wild little shove."
    )
    world.say(
        f"{helper.id} peered at the water and said, \"That current means trouble, and "
        f"those lumber poles could jam together before noon.\""
    )


def boast(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} gave a grin wide enough to hang a moon on. "
        f"\"I can haul this pile faster than a fox can blink,\" {hero.id} boomed."
    )


def warn(world: World, helper: Entity, place: Place, load: Load) -> None:
    helper.memes["caution"] += 1
    pred = predict_jam(world, "load")
    world.facts["predicted_jam"] = pred["jam"]
    world.say(
        f"{helper.id} shook {helper.pronoun('possessive')} head. "
        f"\"Not if the river gets its teeth in it. We need a safer plan.\""
    )


def defy(world: World, hero: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"Still, {hero.id} clapped {hero.pronoun('possessive')} hands and set to work.")


def jam(world: World, river: Entity, load: Entity) -> None:
    _move_load(world, load)
    river.meters["jam"] += 2
    load.meters["stuck"] += 1
    world.say(
        f"The first logs slid out, then locked together with a crack like two giant "
        f"sticks in a king's drum. The lumber jammed the river tight."
    )


def solve(world: World, helper: Entity, hero: Entity, place: Place, plan: Plan, tool: Tool) -> None:
    helper.memes["hope"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"Then {helper.id} pointed at {tool.phrase}. \"We can use that to guide the logs "
        f"one by one,\" {helper.id} said."
    )
    world.say(
        f"{hero.id} gave a new nod, slower and wiser this time. Together they {plan.text}."
    )
    world.get("river").meters["jam"] = 0
    world.get("load").meters["stuck"] = 0
    world.get("load").meters["moved"] += 1


def finish(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"By sunset the river ran free again, the lumber was stacked safely on the far "
        f"bank, and {place.label} smelled like pine and clean rain."
    )
    world.say(
        f"{hero.id} laughed and tipped {hero.pronoun('possessive')} hat. "
        f"\"You were right,\" {hero.id} said. \"A tall tale is fine, but a safe plan is better.\""
    )
    world.say(
        f"{helper.id} smiled, and the two of them marched home with sap on their boots "
        f"and a bright new story in their pockets."
    )


def tell(place: Place, load: Load, tool: Tool, plan: Plan,
         hero_name: str = "Hank", hero_type: str = "boy",
         helper_name: str = "Mabel", helper_type: str = "girl",
         delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hauler"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="watcher"))
    river = world.add(Entity(id="river", kind="thing", type="thing", label="the river", attrs={"storm": place.water}))
    load_ent = world.add(Entity(id="load", kind="thing", type="thing", label=load.label))
    tool_ent = world.add(Entity(id=tool.id, kind="thing", type="thing", label=tool.label))

    start(world, hero, helper, place, load)
    world.para()
    trouble(world, hero, helper, place, load)
    boast(world, hero, helper)
    warn(world, helper, place, load)

    if not load_at_risk(place, load):
        raise StoryError("This lumber tale needs water and a heavy load to make a believable jam.")

    if plan.id == "ignore":
        defy(world, hero)
        world.para()
        jam(world, river, load_ent)
        world.say(
            f"The jam grew larger with every tug, but {helper.id} kept the mood from sinking."
        )
    else:
        defy(world, hero)
        world.para()
        jam(world, river, load_ent)
        solve(world, helper, hero, place, plan, tool_ent)
        world.para()
        finish(world, hero, helper, place)

    world.facts.update(
        hero=hero,
        helper=helper,
        place=place,
        load=load,
        tool=tool,
        plan=plan,
        delay=delay,
        jammed=world.get("load").meters["stuck"] >= THRESHOLD,
        resolved=world.get("river").meters["jam"] == 0,
        storm=place.water,
    )
    return world


PLACES = {
    "riverbank": Place(id="riverbank", label="the riverbank", water=True, windy=True),
    "millyard": Place(id="millyard", label="the mill yard", water=True, windy=False),
    "logging_camp": Place(id="logging_camp", label="the logging camp", water=False, windy=True),
}

LOADS = {
    "planks": Load(id="planks", label="planks", phrase="a pile of pine planks", heavy=True, floating=False, tags={"lumber"}),
    "timbers": Load(id="timbers", label="timbers", phrase="a stack of oak timbers", heavy=True, floating=False, tags={"lumber"}),
    "logs": Load(id="logs", label="logs", phrase="a cartload of round logs", heavy=True, floating=True, tags={"lumber"}),
}

TOOLS = {
    "pole": Tool(id="pole", label="guiding pole", phrase="a long guiding pole", helps={"steady", "push"}, safe=True, tags={"lumber"}),
    "barge": Tool(id="barge", label="little barge", phrase="a little barge with a flat nose", helps={"float", "carry"}, safe=True, tags={"lumber"}),
    "chock": Tool(id="chock", label="wooden chock", phrase="a wooden chock to hold the load", helps={"steady"}, safe=True, tags={"lumber"}),
}

PLANS = {
    "guide_one_by_one": Plan(id="guide_one_by_one", sense=3, power=3, text="used the pole to guide the logs one by one", fail="couldn't steady the logs at all", tags={"lumber"}),
    "float_on_barge": Plan(id="float_on_barge", sense=3, power=4, text="floated the lumber on a little barge and nudged it forward in pieces", fail="watched the barge wobble and list", tags={"lumber"}),
    "chock_and_wait": Plan(id="chock_and_wait", sense=2, power=2, text="wedged the load with chocks and waited for the river to calm", fail="waited too long while the jam tightened", tags={"lumber"}),
    "ignore": Plan(id="ignore", sense=1, power=0, text="ignored the river and pushed harder", fail="ignored the river and pushed harder", tags={"lumber"}),
}

NAMES_BOY = ["Hank", "Eli", "Tom", "Bo", "Finn"]
NAMES_GIRL = ["Mabel", "June", "Ada", "Kit", "Pearl"]
TRAITS = ["bold", "careful", "steady", "clever", "cheerful"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for l in LOADS:
            for t in TOOLS:
                if load_at_risk(PLACES[p], LOADS[l]):
                    out.append((p, l, t))
    return out


@dataclass
class StoryParams:
    place: str
    load: str
    tool: str
    plan: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "lumber": [("What is lumber?", "Lumber is wood that has been cut and shaped so people can build with it. Logs, planks, and beams are all kinds of lumber.")],
    "river": [("What is a river?", "A river is a long stream of moving water. Rivers can carry things downstream and sometimes make travel tricky.")],
    "jam": [("What is a jam in a river?", "A jam is when logs or other things get stuck together and block the water. A jam can stop boats and make a big mess.")],
    "barge": [("What is a barge?", "A barge is a flat boat used to carry heavy things on water. It can help move lumber across a river.")],
    "pole": [("What is a guiding pole for?", "A guiding pole helps push, steer, or steady something heavy. People use it to keep loads from drifting away.")],
    "chock": [("What is a chock?", "A chock is a wedge or block that helps stop something from rolling or sliding. It can keep a load still.")],
    "storm": [("Why is stormy weather tricky for outdoor work?", "Stormy weather can add wind and rough water. That makes it harder and less safe to move heavy things.")],
}
KNOWLEDGE_ORDER = ["lumber", "river", "jam", "barge", "pole", "chock", "storm"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale style story for a child that includes the word "lumber" and ends happily.',
        f"Tell a big, colorful story about {f['hero'].id} and {f['helper'].id} moving lumber near {f['place'].label}, then finding a clever safe way to finish.",
        f"Write a happy ending story where a lumber jam in a river gets solved by teamwork instead of panic.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, place, plan, tool = f["hero"], f["helper"], f["place"], f["plan"], f["tool"]
    qa = [
        ("Who is the story about?", f"It is about {hero.id} and {helper.id}. They worked together near {place.label} to move lumber."),
        ("What problem did they face?", f"The lumber jammed the river and made the job hard. The water and wind pushed the logs together before they could get across."),
        ("How did they solve it?", f"They used {tool.phrase} and {plan.text}. That let them move the lumber in a safer, steadier way."),
    ]
    if f["resolved"]:
        qa.append(("How did the story end?", "It ended happily. The river was clear again, the lumber was stacked safely, and the workers went home proud and smiling."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = []
    tags = set(world.facts["load"].tags) | set(world.facts["tool"].tags)
    if world.facts["place"].water:
        tags.add("river")
        tags.add("storm")
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
    return out


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
    return "\n".join(lines)


CURATED = [
    StoryParams(place="riverbank", load="logs", tool="pole", plan="guide_one_by_one", hero="Hank", hero_type="boy", helper="Mabel", helper_type="girl", trait="bold", delay=0),
    StoryParams(place="millyard", load="timbers", tool="barge", plan="float_on_barge", hero="June", hero_type="girl", helper="Eli", helper_type="boy", trait="steady", delay=0),
    StoryParams(place="riverbank", load="planks", tool="chock", plan="chock_and_wait", hero="Bo", hero_type="boy", helper="Pearl", helper_type="girl", trait="clever", delay=0),
]


def explain_rejection(place: Place, load: Load) -> str:
    return f"(No story: {place.label} needs a heavy lumber load and water to make a believable jam.)"


def explain_plan(plan_id: str) -> str:
    p = PLANS[plan_id]
    return f"(Refusing plan '{plan_id}': it is too weak on common sense (sense={p.sense}).)"


def outcome_of(params: StoryParams) -> str:
    if params.plan == "ignore":
        return "burned"
    return "contained"


ASP_RULES = r"""
valid(P, L, T) :- place(P), load(L), tool(T), water_place(P), heavy_load(L).
sensible_plan(Plan) :- plan(Plan), sense(Plan, S), S >= sense_min.
outcome(contained) :- chosen_plan(Plan), sensible_plan(Plan), not ignored(Plan).
outcome(burned) :- chosen_plan(Plan), ignored(Plan).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.water:
            lines.append(asp.fact("water_place", pid))
    for lid, l in LOADS.items():
        lines.append(asp.fact("load", lid))
        if l.heavy:
            lines.append(asp.fact("heavy_load", lid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
    for pid, p in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("sense", pid, p.sense))
        if pid == "ignore":
            lines.append(asp.fact("ignored", pid))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: clingo gate differs from python valid_combos().")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, load=None, tool=None, plan=None, hero=None, hero_type=None, helper=None, helper_type=None, trait=None, delay=None), _random.Random(7)))
        _ = sample.story
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    else:
        print("OK: verification smoke test completed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale lumber story world with a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--load", choices=LOADS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["boy", "girl"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    place = args.place or rng.choice(sorted(PLACES))
    load = args.load or rng.choice(sorted(LOADS))
    tool = args.tool or rng.choice(sorted(TOOLS))
    plan = args.plan or rng.choice(sorted(PLANS))
    if plan not in PLANS:
        raise StoryError("Unknown plan.")
    if args.plan and not valid_plan(PLANS[args.plan]):
        raise StoryError(explain_plan(args.plan))
    if not load_at_risk(PLACES[place], LOADS[load]):
        raise StoryError(explain_rejection(PLACES[place], LOADS[load]))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    helper_type = args.helper_type or ("girl" if hero_type == "boy" else "boy")
    hero_pool = NAMES_BOY if hero_type == "boy" else NAMES_GIRL
    helper_pool = NAMES_GIRL if helper_type == "girl" else NAMES_BOY
    hero = args.hero or rng.choice(hero_pool)
    helper = args.helper or rng.choice([n for n in helper_pool if n != hero])
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(place=place, load=load, tool=tool, plan=plan, hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type, trait=trait, delay=delay)


def generate(params: StoryParams) -> StorySample:
    for key in ("place", "load", "tool", "plan"):
        if key not in params.__dict__:
            raise StoryError(f"Missing required param: {key}")
    if params.place not in PLACES or params.load not in LOADS or params.tool not in TOOLS or params.plan not in PLANS:
        raise StoryError("Invalid story parameters.")
    world = tell(PLACES[params.place], LOADS[params.load], TOOLS[params.tool], PLANS[params.plan],
                 params.hero, params.hero_type, params.helper, params.helper_type, params.delay)
    return StorySample(params=params, story=world.render(),
                       prompts=generation_prompts(world),
                       story_qa=[QAItem(q, a) for q, a in story_qa(world)],
                       world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
                       world=world)


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
        print(asp_program("", "#show valid/3.\n#show sensible_plan/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show valid/3."))
        print(sorted(asp.atoms(model, "valid")))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
