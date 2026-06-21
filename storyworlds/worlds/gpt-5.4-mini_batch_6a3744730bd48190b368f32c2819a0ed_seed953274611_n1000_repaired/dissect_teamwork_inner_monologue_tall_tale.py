#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dissect_teamwork_inner_monologue_tall_tale.py
===============================================================================

A small tall-tale storyworld: two kids and a helper tackle an impossible-feeling
task together, while inner monologue lets one of them think through the problem
before the team tries the bold, careful "dissect" move.

The premise is intentionally child-facing and safe: they dissect a giant model
object, not anything alive. The world is built around teamwork, a visible turn,
and a strong ending image that proves the work paid off.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/dissect_teamwork_inner_monologue_tall_tale.py
    python storyworlds/worlds/gpt-5.4-mini/dissect_teamwork_inner_monologue_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/dissect_teamwork_inner_monologue_tall_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/dissect_teamwork_inner_monologue_tall_tale.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    body: str
    size: str
    can_dissect: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    sharpness: int
    sense: int
    power: int
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    theme: str = "fair"
    object: str = "balloon"
    tool: str = "saw"
    helper: str = "uncle"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_rise(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["split"] < THRESHOLD:
            continue
        sig = ("rise", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["wonder"] += 1
        out.append("__turn__")
    return out


CAUSAL_RULES = [Rule("rise", _r_rise)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def can_dissect(thing: Thing) -> bool:
    return thing.can_dissect


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for theme in THEMES:
        for oid, obj in OBJECTS.items():
            if not obj.can_dissect:
                continue
            for tid, tool in TOOLS.items():
                if tool.sense >= SENSE_MIN and tool.power >= 1:
                    out.append((theme, oid, tid))
    return out


def _thought(hero: Entity, obj: Thing) -> str:
    if obj.id == "balloon":
        return f"{hero.id} wondered, in the quiet place behind {hero.pronoun('possessive')} eyes, whether the balloon would pop like thunder."
    if obj.id == "map":
        return f"{hero.id} thought, slow as a turtle on a fence post, that a careful cut might reveal where the missing key was hidden."
    return f"{hero.id} thought the big thing looked so puzzling it might hold a whole secret inside it."


def _setup(world: World, a: Entity, b: Entity, helper: Entity, thing: Thing) -> None:
    world.say(
        f"On a day so bright it seemed scrubbed clean by the sky, {a.id} and {b.id} found {thing.phrase} as big as a wagon wheel."
    )
    world.say(
        f"{thing.phrase.capitalize()} sat there like it had a riddle in its pocket, and the three of them meant to dissect it and see what was tucked away inside."
    )
    world.say(_thought(a, thing))


def _warn(world: World, helper: Entity, a: Entity, thing: Thing) -> None:
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} scratched {helper.pronoun('possessive')} chin and said, \"Careful now. We can dissect it, but only if we do it together and keep the pieces neat.\""
    )
    world.say(
        f"{a.id} listened, and the idea grew steadier in {a.pronoun('possessive')} chest."
    )


def _do_work(world: World, a: Entity, b: Entity, helper: Entity, thing: Thing, tool: Tool) -> None:
    a.meters["split"] += 1
    b.meters["held"] += 1
    helper.meters["guided"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the team went to work: {a.id} used {tool.phrase}, {b.id} held the thing still, and {helper.id} counted the beats like a town crier counting bells."
    )
    world.say(
        f"{tool.text.replace('{object}', thing.label)}"
    )


def _finish(world: World, a: Entity, b: Entity, helper: Entity, thing: Thing) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"When the last careful slice was done, the thing opened like a storybook, and out tumbled the little treasure it had been hiding."
    )
    world.say(
        f"{a.id} grinned, {b.id} clapped, and {helper.id} laughed so hard the fence posts seemed to chuckle along."
    )
    world.say(
        f"By sunset, the bits were lined up neat as dominoes, and the whole team stood there with dusty hands and bright eyes, proud they had dissected the giant mystery together."
    )


def _fail(world: World, a: Entity, b: Entity, helper: Entity, thing: Thing, tool: Tool) -> None:
    world.say(
        f"{tool.fail.replace('{object}', thing.label)}"
    )
    world.say(
        f"The thing wobbled, then the team tried again, this time slower and kinder, because tall tales teach that steady hands beat hurried ones every time."
    )


def tell(theme: str, obj: Thing, tool: Tool, helper_name: str) -> World:
    world = World()
    a = world.add(Entity(id="Nell", kind="character", type="girl", role="thinker", traits=["curious"]))
    b = world.add(Entity(id="Bo", kind="character", type="boy", role="helper", traits=["steady"]))
    helper = world.add(Entity(id=helper_name, kind="character", type="man", role="helper", traits=["wise"]))
    world.add(Entity(id="table", type="thing", label="the worktable"))
    world.facts.update(theme=theme, object=obj, tool=tool, helper=helper)

    world.say(f"This was a tall tale kind of afternoon, the kind where the wind looked like it had combed its hair just for the occasion.")
    _setup(world, a, b, helper, obj)
    world.para()
    _warn(world, helper, a, obj)
    world.para()
    _do_work(world, a, b, helper, obj, tool)
    if obj.id == "balloon":
        world.say("A tiny hush fell over the room, because everyone was listening for the secret.")
    world.para()
    if tool.power >= 1:
        _finish(world, a, b, helper, obj)
    else:
        _fail(world, a, b, helper, obj, tool)

    world.facts.update(
        a=a, b=b, helper=helper, obj=obj, tool=tool,
        split=a.meters["split"] >= THRESHOLD,
    )
    return world


THEMES = {
    "fair": "a county fair with banners big as bedsheets",
    "harbor": "a harbor where the boats bobbed like buttons in a bucket",
    "prairie": "a prairie town with a sky wide enough to lose a hat in",
}

OBJECTS = {
    "balloon": Thing(id="balloon", label="balloon", phrase="a giant parade balloon", body="rubber", size="huge", can_dissect=True, tags={"balloon"}),
    "map": Thing(id="map", label="map", phrase="a folded treasure map", body="paper", size="large", can_dissect=True, tags={"map"}),
    "kite": Thing(id="kite", label="kite", phrase="a sky-blue kite", body="cloth", size="large", can_dissect=True, tags={"kite"}),
}

TOOLS = {
    "saw": Tool(id="saw", label="handsaw", phrase="a handsaw", sharpness=3, sense=3, power=2,
                text="The saw sang a little saw-song, and the seam split open just enough to peek inside the {object}.",
                fail="The saw skated sideways and only scratched the {object}, which was no good at all.", tags={"tool"}),
    "scissors": Tool(id="scissors", label="scissors", phrase="big scissors", sharpness=2, sense=2, power=1,
                     text="The scissors snipped with mouse-soft bites, and soon the {object} opened up like a shy flower.",
                     fail="The scissors nipped at the {object} but could not make a clean path.", tags={"tool"}),
    "knife": Tool(id="knife", label="knife", phrase="a dull paring knife", sharpness=2, sense=2, power=1,
                  text="The knife worked slowly, and the {object} gave way as politely as a door held for a guest.",
                  fail="The knife was too clumsy, and the {object} stayed shut tight as a drum.", tags={"tool"}),
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    obj: Thing = f["obj"]
    tool: Tool = f["tool"]
    return [
        f'Write a tall tale for a child that includes the word "dissect" and shows teamwork around {obj.phrase}.',
        f"Tell a story where two children and a helper dissect {obj.phrase} together using {tool.phrase}.",
        f"Write a careful, funny tall tale with inner monologue where someone wonders what is inside {obj.phrase} before the team opens it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, helper, obj, tool = f["a"], f["b"], f["helper"], f["obj"], f["tool"]
    return [
        QAItem(
            question="Who worked together in the story?",
            answer=f"{a.id}, {b.id}, and {helper.id} worked together. They each did a different job, and that teamwork is what made the big job possible."
        ),
        QAItem(
            question="What did the team want to do?",
            answer=f"They wanted to dissect {obj.phrase} carefully. They were trying to see what secret or treasure was hidden inside."
        ),
        QAItem(
            question=f"What was {a.id} thinking before they started?",
            answer=f"{a.id} was thinking carefully about what the big thing might hide. That inner monologue helped {a.id} slow down and choose a safe, steady way to begin."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the {obj.label} opened and the little treasure laid out neat as can be. The team stood together, proud of the job they finished."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    obj: Thing = f["obj"]
    tool: Tool = f["tool"]
    items = [
        QAItem(
            question="What does dissect mean?",
            answer="To dissect something means to carefully take it apart or cut it open so you can look at how it is made."
        ),
        QAItem(
            question="Why do helpers work together on a big job?",
            answer="Big jobs can be safer and easier when people share the work. One person can hold, one can think, and one can do the careful cutting."
        ),
        QAItem(
            question="What should you do before using a sharp tool?",
            answer="You should slow down, listen to the plan, and make sure an adult or helper is nearby. Careful hands matter more than fast hands."
        ),
    ]
    if obj.id == "balloon":
        items.append(QAItem(
            question="What is a balloon?",
            answer="A balloon is a stretchy object that can hold air and get big. Big balloons are often used in parades and fairs."
        ))
    if tool.id == "saw":
        items.append(QAItem(
            question="What is a handsaw for?",
            answer="A handsaw is a tool people use for cutting through certain materials in a careful back-and-forth way."
        ))
    return items


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the chosen object or tool does not make a sensible, safe dissecting tale.)"


def valid_story(params: StoryParams) -> bool:
    return params.theme in THEMES and params.object in OBJECTS and params.tool in TOOLS and TOOLS[params.tool].sense >= SENSE_MIN and can_dissect(OBJECTS[params.object])


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale teamwork storyworld with inner monologue and a safe dissecting task.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper")
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
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(f"(Refusing tool '{args.tool}': it is too awkward for this story.)")
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.object is None or c[1] == args.object)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, obj, tool = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(["Uncle Ray", "Aunt June", "Mr. Hoot"])
    return StoryParams(theme=theme, object=obj, tool=tool, helper=helper)


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError(explain_rejection(params))
    world = tell(THEMES[params.theme], OBJECTS[params.object], TOOLS[params.tool], params.helper)
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
valid(T,O,U) :- theme(T), object(O), tool(U), sense(U,S), sense_min(M), S >= M, can_dissect(O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.can_dissect:
            lines.append(asp.fact("can_dissect", oid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, t.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid-combos disagree.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), _random.Random(0)))
        assert sample.story
    except Exception as e:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: ASP parity and story-generation smoke test passed.")
    return rc


CURATED = [
    StoryParams(theme="fair", object="balloon", tool="saw", helper="Uncle Ray"),
    StoryParams(theme="harbor", object="map", tool="scissors", helper="Aunt June"),
    StoryParams(theme="prairie", object="kite", tool="knife", helper="Mr. Hoot"),
]


def asp_outcome(params: StoryParams) -> str:
    return "valid" if valid_story(params) else "invalid"


def generation_params_list() -> list[StoryParams]:
    return CURATED


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for t, o, u in asp_valid_combos():
            print(f"{t} {o} {u}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in generation_params_list()]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
