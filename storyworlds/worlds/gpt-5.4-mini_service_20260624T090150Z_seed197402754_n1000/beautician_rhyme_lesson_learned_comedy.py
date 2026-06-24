#!/usr/bin/env python3
"""
A small comedy story world about a beautician, a rhyme, and a lesson learned.

The tale premise:
- A beautician is trying to get a client ready.
- A funny rhyme helps them remember the right order of steps.
- A small mix-up creates a comic mess.
- The beauty work is saved, and the lesson is learned.

This script follows the Storyweavers contract with:
- a simulated world model
- a Python reasonableness gate
- an inline ASP twin
- story, QA, trace, JSON, and verify modes
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
    worn_by: Optional[str] = None
    target: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "girl", "mother", "aunt"}
        male = {"man", "boy", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    task: str
    tool: str
    name: str
    client_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


def _rule_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        for task in TASKS.values():
            if actor.meters.get(task.mess, 0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.id == "client_cape":
                    if item.target == actor.id and task.mess in item.guards:
                        continue
                sig = ("mess", actor.id, task.id)
                if sig in world.fired:
                    continue
                if item.id == "client_cape":
                    continue
                world.fired.add(sig)
                item.meters[task.mess] = item.meters.get(task.mess, 0) + 1
                item.meters["dirty"] = item.meters.get("dirty", 0) + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {task.mess} and dirty.")
    return out


def _rule_stain_cape(world: World) -> list[str]:
    out: list[str] = []
    client = next((e for e in world.entities.values() if e.id == "client"), None)
    cape = world.entities.get("cape")
    if not client or not cape:
        return out
    if client.meters.get("mess", 0) < THRESHOLD:
        return out
    if cape.target != client.id:
        return out
    if "mess" in cape.guards:
        return out
    sig = ("cape",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cape.meters["dirty"] = cape.meters.get("dirty", 0) + 1
    out.append("The cape ended up spotted too.")
    return out


def _rule_cleanup(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("dirty", 0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("cleanup", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        cleaner = world.get(item.caretaker)
        cleaner.meters["work"] = cleaner.meters.get("work", 0) + 1
        out.append(f"That meant more work for {cleaner.label}.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in RULES:
            sents = fn(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def chance_line(task: Task) -> str:
    return {
        "hair": "The comb went click-clack, and the mirror felt like it was giggling.",
        "nails": "The nail polish made tiny shining moons on every fingertip.",
        "makeup": "The brush swished like a sleepy cat tail.",
        "braid": "The braid twirled into a neat ribbon of hair.",
    }.get(task.id, "The room felt busy and funny.")


def setting_detail(setting: Setting) -> str:
    if setting.indoors:
        return f"Inside {setting.place}, the chairs lined up like they were waiting for a joke."
    return f"{setting.place.capitalize()} was bright, with a chair and a mirror ready for business."


def task_at_risk(task: Task, tool: Tool) -> bool:
    return bool(task.zone & tool.covers)


def select_tool(task: Task, tool_id: str) -> Optional[Tool]:
    tool = TOOLS[tool_id]
    if task.mess in tool.guards and task.zone <= tool.covers:
        return tool
    return None


def predict_mess(world: World, actor: Entity, task: Task, client_id: str) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get(actor.id), task, narrate=False)
    client = sim.entities.get(client_id)
    return {"soiled": bool(client and client.meters.get("dirty", 0) >= THRESHOLD)}


def _do_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    if task.id not in world.setting.affords:
        return
    world.zone = set(task.zone)
    actor.meters[task.mess] = actor.meters.get(task.mess, 0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, beautician: Entity) -> None:
    world.say(f"{beautician.id} was a cheerful beautician who liked neat parts, shiny clips, and good jokes.")


def loves_task(world: World, beautician: Entity, task: Task) -> None:
    world.say(f"{beautician.pronoun().capitalize()} loved {task.gerund}, because {chance_line(task)}")


def client_arrives(world: World, client: Entity, beautician: Entity) -> None:
    world.say(f"One day, {client.id} sat in the chair while {beautician.id} brushed {client.pronoun('possessive')} hair.")


def rhyme(world: World, beautician: Entity, task: Task, tool: Tool) -> None:
    beautician.memes["rhyme"] = beautician.memes.get("rhyme", 0) + 1
    world.say(
        f'{beautician.id} sang, "Clip, clip, zip-zip, slow your hands and keep your grip; '
        f'{tool.prep}, and then do {task.verb} with a happy skip."'
    )


def warning(world: World, beautician: Entity, client: Entity, task: Task, tool: Tool) -> bool:
    pred = predict_mess(world, beautician, task, client.id)
    if not pred["soiled"]:
        return False
    world.facts["warning"] = True
    world.say(
        f'"Careful," {beautician.id} said with a laugh. "If I rush, {client.id} might get {task.soil}."'
    )
    return True


def fumble(world: World, beautician: Entity, task: Task) -> None:
    beautician.memes["flustered"] = beautician.memes.get("flustered", 0) + 1
    world.say(f"{beautician.id} rushed anyway and nearly used the wrong thing.")
    world.say(f"{beautician.id} tried to {task.rush}.")


def fix(world: World, beautician: Entity, client: Entity, task: Task, tool: Tool) -> None:
    beautician.memes["lesson"] = beautician.memes.get("lesson", 0) + 1
    world.say(
        f"Then {beautician.id} blinked, laughed at the silly mistake, and remembered the rhyme."
    )
    world.say(
        f"{beautician.id} used {tool.label} first, and soon {client.id} was {task.gerund} without any fuss."
    )
    world.say(
        f"In the mirror, {client.id} looked tidy and happy, and {beautician.id} learned to go slow when the joke was on."
    )


def tell(setting: Setting, task: Task, tool_cfg: Tool, beautician_name: str, client_name: str) -> World:
    world = World(setting)
    beautician = world.add(Entity(id=beautician_name, kind="character", type="woman", label="the beautician"))
    client = world.add(Entity(id=client_name, kind="character", type="child", label="the client"))
    cape = world.add(Entity(id="cape", type="cape", label="cape", caretaker=beautician.id, owner=client.id, target=client.id))
    world.say(f"{beautician.id} worked at {setting.place} and loved making people look fancy.")
    world.para()
    introduce(world, beautician)
    loves_task(world, beautician, task)
    client_arrives(world, client, beautician)
    world.say(setting_detail(setting))
    world.para()
    rhyme(world, beautician, task, tool_cfg)
    warning(world, beautician, client, task, tool_cfg)
    fumble(world, beautician, task)
    _do_task(world, beautician, task, narrate=True)
    world.para()
    fix(world, beautician, client, task, tool_cfg)
    cape.worn_by = client.id
    cape.meters["dirty"] = cape.meters.get("dirty", 0)
    world.facts.update(
        beautician=beautician,
        client=client,
        cape=cape,
        task=task,
        tool=tool_cfg,
        setting=setting,
        resolved=True,
    )
    return world


SETTINGS = {
    "salon": Setting(place="the salon", indoors=True, affords={"hair", "nails", "makeup"}),
    "shop": Setting(place="the beauty shop", indoors=True, affords={"hair", "nails"}),
}

TASKS = {
    "hair": Task(
        id="hair",
        verb="trim the bangs",
        gerund="trimming bangs",
        rush="snip the fringe too fast",
        mess="hair",
        soil="a crooked mess of hair",
        zone={"head"},
        keyword="clip",
        tags={"hair", "comedy"},
    ),
    "nails": Task(
        id="nails",
        verb="paint the nails",
        gerund="painting nails",
        rush="swirl the polish too fast",
        mess="paint",
        soil="polish on the fingers and chair",
        zone={"hands"},
        keyword="paint",
        tags={"nails", "comedy"},
    ),
    "makeup": Task(
        id="makeup",
        verb="dab on blush",
        gerund="dabbing blush",
        rush="tap the brush too fast",
        mess="powder",
        soil="powder on the nose",
        zone={"cheeks"},
        keyword="brush",
        tags={"makeup", "comedy"},
    ),
}

TOOLS = {
    "comb": Tool(id="comb", label="the wide comb", covers={"head"}, guards={"hair"}, prep="comb slowly from the ends up", tail="finished with the wide comb"),
    "gloves": Tool(id="gloves", label="tiny gloves", covers={"hands"}, guards={"paint"}, prep="put on tiny gloves", tail="swapped to the tiny gloves"),
    "powder_puff": Tool(id="powder_puff", label="a soft powder puff", covers={"cheeks"}, guards={"powder"}, prep="use a soft powder puff", tail="used the soft powder puff"),
}

RULES = [_rule_mess, _rule_stain_cape, _rule_cleanup]

PRINCIPLES = {
    "hair": "Slow hands make neater bangs.",
    "nails": "If paint stays on the nails, it stays off the sleeves.",
    "makeup": "A soft touch keeps the powder where it belongs.",
}

@dataclass
class StoryWorldFacts:
    pass


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            task = TASKS[task_id]
            for tool_id, tool in TOOLS.items():
                if task_at_risk(task, tool) and select_tool(task, tool_id):
                    combos.append((place, task_id, tool_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    t = f["task"]
    return [
        f'Write a short comedy story for a young child about a beautician who remembers a rhyme while {t.gerund}.',
        f'Tell a funny story where {f["beautician"].id} helps {f["client"].id} at {f["setting"].place} and learns a lesson after a small mix-up.',
        f'Write a simple story that includes the word "{t.keyword}" and ends with a lesson learned in a cheerful beauty shop.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    b = f["beautician"]
    c = f["client"]
    t = f["task"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {b.id}, a beautician, and {c.id}, the client in the chair.",
        ),
        QAItem(
            question=f"What rhyme did {b.id} use before {t.verb}?",
            answer=f"{b.id} sang a funny rhyme about going slow and using {tool.label} first.",
        ),
        QAItem(
            question=f"What lesson did {b.id} learn?",
            answer=f"{b.id} learned to slow down and follow the rhyme so the beauty work stayed neat and funny, not messy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    t = f["task"]
    tool = f["tool"]
    return [
        QAItem(
            question="What does a beautician do?",
            answer="A beautician helps people with hair, nails, makeup, and other parts of getting ready.",
        ),
        QAItem(
            question=f"Why is {tool.label} helpful?",
            answer=f"{tool.label.capitalize()} is helpful because it protects the right part while someone works carefully.",
        ),
        QAItem(
            question=f"Why should someone go slow when {t.gerund}?",
            answer=f"Going slow helps keep {t.soil} from happening, and it makes the result look neat.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.target:
            bits.append(f"target={e.target}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="salon", task="hair", tool="comb", name="Mina", client_name="Pip"),
    StoryParams(place="shop", task="nails", tool="gloves", name="Tessa", client_name="Bo"),
    StoryParams(place="salon", task="makeup", tool="powder_puff", name="Rina", client_name="Dot"),
]


def explain_rejection(task: Task, tool: Tool) -> str:
    return f"(No story: {tool.label} does not reasonably solve {task.gerund}.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("mess_of", tid, t.mess))
        for r in sorted(t.zone):
            lines.append(asp.fact("zone", tid, r))
    for uid, u in TOOLS.items():
        lines.append(asp.fact("tool", uid))
        for c in sorted(u.covers):
            lines.append(asp.fact("covers", uid, c))
        for g in sorted(u.guards):
            lines.append(asp.fact("guards", uid, g))
    return "\n".join(lines)


ASP_RULES = r"""
task_at_risk(T, U) :- zone(T, R), covers(U, R).
valid_combo(P, T, U) :- affords(P, T), task_at_risk(T, U), mess_of(T, M), guards(U, M).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy story world about a beautician, a rhyme, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--client-name")
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
    if args.task and args.tool:
        task, tool = TASKS[args.task], TOOLS[args.tool]
        if not (task_at_risk(task, tool) and select_tool(task, args.tool)):
            raise StoryError(explain_rejection(task, tool))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task_id, tool_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(["Mina", "Tessa", "Rina", "Lola", "Nia", "June"])
    client_name = args.client_name or rng.choice(["Pip", "Bo", "Dot", "Max", "Eli", "Zed"])
    return StoryParams(place=place, task=task_id, tool=tool_id, name=name, client_name=client_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task], TOOLS[params.tool], params.name, params.client_name)
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
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, task, tool) combos:\n")
        for p, t, u in combos:
            print(f"  {p:8} {t:10} {u}")
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
            header = f"### {p.name}: {p.task} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
