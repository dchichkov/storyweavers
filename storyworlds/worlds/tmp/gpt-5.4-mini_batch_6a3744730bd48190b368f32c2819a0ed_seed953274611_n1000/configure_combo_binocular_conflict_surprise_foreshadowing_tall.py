#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/configure_combo_binocular_conflict_surprise_foreshadowing_tall.py
===================================================================================================

A tiny tall-tale storyworld about a boastful contest, a tricky setup, a pair of
binoculars, and a surprising twist that was foreshadowed all along.

The domain is small on purpose: a child at a county fair wants to "configure"
a contraption, a rival objects, and a looming stage show becomes the test.  The
story engine models typed entities with physical meters and emotional memes, and
it narrates from changing world state rather than swapping nouns in a frozen
paragraph.

The seed words are all present in the world model and prose:
- configure
- combo
- binocular

The story features:
- conflict
- surprise
- foreshadowing

Style: tall tale, child-facing, concrete, and a little larger than life.
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    stage: str
    crowd: str
    sky_sign: str


@dataclass
class Rig:
    id: str
    name: str
    parts: list[str]
    safe: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    where: str
    helps: str
    flashy: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Dilemma:
    id: str
    label: str
    conflict_text: str
    surprise_text: str
    foreshadow_text: str
    danger: int
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


def _r_nervous(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["worry"] >= THRESHOLD and ("nervous", e.id) not in world.fired:
            world.fired.add(("nervous", e.id))
            out.append("__nervous__")
    return out


def _r_shine(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["shine"] >= THRESHOLD and ("shine", e.id) not in world.fired:
            world.fired.add(("shine", e.id))
            out.append("__shine__")
    return out


CAUSAL_RULES = [Rule("nervous", "social", _r_nervous), Rule("shine", "physical", _r_shine)]


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


def valid_combo(setting: Setting, rig: Rig, dilemma: Dilemma) -> bool:
    return (not rig.safe) and ("binocular" in rig.tags) and ("configure" in dilemma.tags)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def conflict_gate(dilemma: Dilemma, rig: Rig) -> bool:
    return ("conflict" in dilemma.tags) and ("binocular" in rig.tags)


def predict_show(world: World, rig_id: str) -> dict:
    sim = world.copy()
    _do_configure(sim, sim.get(rig_id), narrate=False)
    return {"shine": sim.get(rig_id).meters["shine"] >= THRESHOLD, "worry": sum(e.memes["worry"] for e in sim.entities.values())}


def _do_configure(world: World, rig: Entity, narrate: bool = True) -> None:
    rig.meters["shine"] += 1
    rig.memes["confidence"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, kid: Entity, rival: Entity, setting: Setting) -> None:
    kid.memes["joy"] += 1
    rival.memes["joy"] += 1
    world.say(
        f"On the widest afternoon the county fair ever saw, {kid.id} and {rival.id} met at {setting.place}. "
        f"{setting.stage} stood there like a wooden hill, and {setting.sky_sign} bobbed above the crowd."
    )


def foreshadow(world: World, kid: Entity, dilemma: Dilemma, tool: Tool) -> None:
    kid.memes["worry"] += 1
    world.say(
        f"A little warning had already been hanging in the air. Near the ticket booth sat {tool.phrase}, "
        f"and the old sign by the ringmaster's wagon muttered, '{dilemma.foreshadow_text}'."
    )


def conflict(world: World, kid: Entity, rival: Entity, dilemma: Dilemma, tool: Tool) -> None:
    kid.memes["defiance"] += 1
    rival.memes["worry"] += 1
    world.say(
        f'{kid.id} wanted to {dilemma.label} with the {tool.label} and said, "I can {dilemma.label} if I configure the combo just right."'
    )
    world.say(
        f'But {rival.id} shook {rival.pronoun("possessive")} head. "{dilemma.conflict_text}"'
    )


def surprise(world: World, parent: Entity, kid: Entity, rig: Rig, tool: Tool, dilemma: Dilemma) -> None:
    world.say(
        f"Then came the surprise. {parent.label_word.capitalize()} stepped up, smiled, and revealed that {tool.label} had been brought for a reason."
    )
    world.say(
        f'"{dilemma.surprise_text}," {parent.id} said. "The show needs a clever combo, not a wild guess."'
    )


def rescue(world: World, parent: Entity, response: Response, rig: Entity, dilemma: Dilemma) -> None:
    rig.meters["shine"] = 0
    world.say(f"{parent.label_word.capitalize()} helped at once and {response.text}.")
    world.say(
        f"The stage lanterns settled down, and the whole fair breathed easier as the dust sparkled like sugar."
    )


def lesson(world: World, parent: Entity, kid: Entity, rival: Entity, dilemma: Dilemma) -> None:
    kid.memes["relief"] += 1
    rival.memes["relief"] += 1
    world.say(
        f"Then {parent.label_word.capitalize()} knelt down and gave them both a wink. "
        f'"Bragging can make a tall idea wobble," {parent.pronoun()} said, "but a good plan keeps it standing."'
    )
    world.say(
        f'{kid.id} nodded. "{dilemma.label.capitalize()} first, then {tool_phrase_for_lesson(world)}," {kid.id} said, and the crowd cheered.'
    )


def tool_phrase_for_lesson(world: World) -> str:
    tool = world.facts["tool"]
    return f"configure the combo with the {tool.label}"


def ending(world: World, kid: Entity, rival: Entity, setting: Setting) -> None:
    world.say(
        f"By sunset the {setting.crowd} had gone home, the {setting.stage} was quiet, and {kid.id}'s binoculars shone on the table like two polished moons."
    )
    world.say(
        f"{kid.id} and {rival.id} watched the last kite drift over the fairgrounds, both grinning at the same time."
    )


def tell(setting: Setting, rig: Rig, tool: Tool, dilemma: Dilemma, response: Response,
         kid_name: str = "Mabel", kid_gender: str = "girl",
         rival_name: str = "Hank", rival_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World()
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_gender, role="kid"))
    rival = world.add(Entity(id=rival_name, kind="character", type=rival_gender, role="rival"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent"))
    tool_ent = world.add(Entity(id=tool.id, type="tool", label=tool.label))
    rig_ent = world.add(Entity(id=rig.id, type="rig", label=rig.name))
    world.facts.update(setting=setting, rig=rig, tool=tool, dilemma=dilemma, response=response, kid=kid, rival=rival, parent=parent)

    setup(world, kid, rival, setting)
    world.para()
    foreshadow(world, kid, dilemma, tool)
    conflict(world, kid, rival, dilemma, tool)

    if "avert" in dilemma.tags:
        world.para()
        surprise(world, parent, kid, rig, tool, dilemma)
        _do_configure(world, rig_ent)
        rescue(world, parent, response, rig_ent, dilemma)
    else:
        world.para()
        surprise(world, parent, kid, rig, tool, dilemma)
        _do_configure(world, rig_ent)
        if response.power >= dilemma.danger:
            rescue(world, parent, response, rig_ent, dilemma)
        else:
            world.say(f"{parent.label_word.capitalize()} tried to help, but the trouble had grown too tall to catch.")
            world.say("The fairground crew had to steady the rig with ropes while everybody backed away.")
    world.para()
    lesson(world, parent, kid, rival, dilemma)
    ending(world, kid, rival, setting)
    return world


SETTINGS = {
    "fair": Setting(id="fair", place="the county fair", stage="the stage", crowd="crowd", sky_sign="a crooked weather vane"),
    "rodeo": Setting(id="rodeo", place="the rodeo grounds", stage="the bucking pen", crowd="grandstand folks", sky_sign="a tin star"),
}

RIGS = {
    "combo": Rig(id="combo", name="a combo rig", parts=["lantern", "rope", "pulley"], safe=False, tags={"combo", "configure", "binocular"}),
    "tower": Rig(id="tower", name="a tall tower", parts=["boards", "hooks"], safe=False, tags={"configure"}),
}

TOOLS = {
    "binocular": Tool(id="binocular", label="binocular", phrase="a pair of binoculars", where="on the table", helps="helps spot the far-off cue", flashy=True, tags={"binocular", "configure"}),
    "whistle": Tool(id="whistle", label="whistle", phrase="a silver whistle", where="around the neck of the boothkeeper", helps="calls the crowd", flashy=False, tags=set()),
}

DILEMMAS = {
    "conflict": Dilemma(id="conflict", label="configure", conflict_text="That combo will wobble if you rush it.", surprise_text="The binoculars were not for show at all; they were for lining up the pulleys.", foreshadow_text="When the goggles come out, the tall trick gets tested.", danger=2, tags={"conflict", "configure", "binocular"}),
    "surprise": Dilemma(id="surprise", label="combo", conflict_text="A combo can be clever, but only if every piece is snug.", surprise_text="The tallest part was hollow, and the binoculars were meant to be the secret eye.", foreshadow_text="A surprise waits inside any big boast.", danger=2, tags={"surprise", "combo", "binocular"}),
}

RESPONSES = {
    "steady": Response(id="steady", sense=3, power=3, text="steadied the rig with a rope and a practiced hand", fail="could not steady the rig in time", qa_text="steadied the rig with a rope and a practiced hand", tags={"steady"}),
    "stomp": Response(id="stomp", sense=1, power=1, text="stomped the dust, but that was no answer at all", fail="stomped the dust, but that was no answer at all", qa_text="stomped the dust", tags={"stomp"}),
    "brace": Response(id="brace", sense=3, power=4, text="braced the tall rig with a beam from the wagon", fail="braced the tall rig, but the trouble was already too great", qa_text="braced the tall rig with a beam from the wagon", tags={"brace"}),
}

GIRL_NAMES = ["Mabel", "June", "Pearl", "Nell", "Daisy", "Ruth"]
BOY_NAMES = ["Hank", "Otis", "Benny", "Lem", "Clyde", "Rufus"]


@dataclass
class StoryParams:
    setting: str
    rig: str
    tool: str
    dilemma: str
    response: str
    kid_name: str
    kid_gender: str
    rival_name: str
    rival_gender: str
    parent_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for rid, rig in RIGS.items():
            for did, dilemma in DILEMMAS.items():
                if valid_combo(setting, rig, dilemma):
                    combos.append((sid, rid, did))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld with conflict, surprise, and foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--rig", choices=RIGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--dilemma", choices=DILEMMAS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--kid-name")
    ap.add_argument("--kid-gender", choices=["girl", "boy"])
    ap.add_argument("--rival-name")
    ap.add_argument("--rival-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("That response is too weak for this tall tale.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.rig is None or c[1] == args.rig)
              and (args.dilemma is None or c[2] == args.dilemma)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, rig, dilemma = rng.choice(sorted(combos))
    tool = args.tool or "binocular"
    response = args.response or rng.choice([r.id for r in sensible_responses()])
    kid_gender = args.kid_gender or "girl"
    rival_gender = args.rival_gender or "boy"
    kid_name = args.kid_name or rng.choice(GIRL_NAMES if kid_gender == "girl" else BOY_NAMES)
    rival_name = args.rival_name or rng.choice(BOY_NAMES if rival_gender == "boy" else GIRL_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, rig=rig, tool=tool, dilemma=dilemma, response=response,
                       kid_name=kid_name, kid_gender=kid_gender, rival_name=rival_name,
                       rival_gender=rival_gender, parent_type=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a child that includes the words "configure", "combo", and "binocular".',
        f"Tell a story where {f['kid'].id} tries to configure a combo rig with binoculars, gets into a conflict, and then faces a surprise.",
        f"Write a foreshadowed fairground tale where a big idea needs binoculars, a rival warns of trouble, and the ending stays playful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid, rival, parent = f["kid"], f["rival"], f["parent"]
    dilemma, tool, response = f["dilemma"], f["tool"], f["response"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {kid.id}, {rival.id}, and the grown-up who stepped in when the fairground trouble started."
        ),
        QAItem(
            question=f"What did {kid.id} want to do?",
            answer=f"{kid.id} wanted to configure the combo so the binocular trick would work. That idea mattered because the show was waiting and the crowd was watching."
        ),
        QAItem(
            question="What was the surprise?",
            answer=f"The surprise was that {tool.phrase} were actually part of the plan, not a joke. They helped line up the rig so the whole contraption could work."
        ),
        QAItem(
            question="How was the conflict solved?",
            answer=f"{parent.label_word.capitalize()} helped {response.qa_text}, which kept the show from wobbling too far. The danger settled down and the crowd could breathe again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What are binoculars?", answer="Binoculars are two little lenses you hold up to your eyes so you can see far away things more clearly."),
        QAItem(question="What is a combo?", answer="A combo is a clever mix of things that work together as one plan or one team."),
        QAItem(question="What does configure mean?", answer="To configure something means to arrange its parts in the right way so it works the way you want."),
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="fair", rig="combo", tool="binocular", dilemma="conflict", response="steady",
                kid_name="Mabel", kid_gender="girl", rival_name="Hank", rival_gender="boy", parent_type="mother"),
    StoryParams(setting="rodeo", rig="combo", tool="binocular", dilemma="surprise", response="brace",
                kid_name="Daisy", kid_gender="girl", rival_name="Rufus", rival_gender="boy", parent_type="father"),
]


def tell_story(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    rig = RIGS[params.rig]
    tool = TOOLS[params.tool]
    dilemma = DILEMMAS[params.dilemma]
    response = RESPONSES[params.response]
    world = tell(setting, rig, tool, dilemma, response, params.kid_name, params.kid_gender, params.rival_name, params.rival_gender, params.parent_type)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
valid(S,R,D) :- setting(S), rig(R), dilemma(D), binocular_rig(R), configure_dilemma(D).
sensible_response(R) :- response(R), sense(R, N), min_sense(M), N >= M.
outcome(ok) :- sensible_response(steady).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid, rig in RIGS.items():
        lines.append(asp.fact("rig", rid))
        if "binocular" in rig.tags:
            lines.append(asp.fact("binocular_rig", rid))
    for did, d in DILEMMAS.items():
        lines.append(asp.fact("dilemma", did))
        if "configure" in d.tags:
            lines.append(asp.fact("configure_dilemma", did))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("min_sense", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_response/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_response"))


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: clingo gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible response set matches.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def explain_rejection() -> str:
    return "This combination does not make a good tall tale."


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible_response/1."))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
