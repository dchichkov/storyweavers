#!/usr/bin/env python3
"""
A standalone storyworld for a small mystery set in a workshop.

Premise:
A curious child notices a strange clue in a workshop: a sponge can absorb a spill,
a board can bias a result, and a loud smack can reveal who touched what. The child
follows clues, doubts first impressions, and helps two workshop friends reconcile
after a mix-up.

This world keeps the story grounded in physical meters and emotional memes:
- physical: wetness, dust, paint, noise, neatness, evidence
- emotional: curiosity, worry, bias, blame, relief, reconciliation
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the workshop"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    sound: str
    clue: str
    weather: str = ""
    keyword: str = ""
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "workshop": Setting(place="the workshop", affords={"glue", "paint", "wood"}),
}

ACTIVITIES = {
    "glue": Activity(
        id="glue",
        verb="fix the model with glue",
        gerund="fixing the model with glue",
        mess="sticky",
        sound="smack",
        clue="a sticky fingerprint",
        keyword="glue",
        tags={"mystery", "smack", "absorb"},
    ),
    "paint": Activity(
        id="paint",
        verb="paint the sign",
        gerund="painting the sign",
        mess="painted",
        sound="smack",
        clue="a bright paint streak",
        keyword="paint",
        tags={"mystery", "smack", "absorb"},
    ),
    "wood": Activity(
        id="wood",
        verb="sand the wooden box",
        gerund="sanding the wooden box",
        mess="dusty",
        sound="smack",
        clue="a dusty handprint",
        keyword="wood",
        tags={"mystery", "smack", "bias"},
    ),
}

PRIZES = {
    "notebook": {"label": "notebook", "phrase": "a neat blue notebook", "region": "torso", "plural": False},
    "apron": {"label": "apron", "phrase": "a clean apron", "region": "torso", "plural": False},
    "gloves": {"label": "gloves", "phrase": "pair of white gloves", "region": "hands", "plural": True},
}

TOOLS = [
    Tool(
        id="sponge",
        label="a sponge",
        covers={"hands"},
        guards={"sticky", "painted", "dusty"},
        prep="take out a sponge first",
        tail="used the sponge to soak up the spill",
    ),
    Tool(
        id="rag",
        label="a soft rag",
        covers={"hands"},
        guards={"sticky", "painted"},
        prep="set out a soft rag first",
        tail="carefully wiped the bench clean",
    ),
    Tool(
        id="tray",
        label="a shallow tray",
        covers={"torso"},
        guards={"dusty"},
        prep="place the pieces on a shallow tray first",
        tail="moved the parts onto the tray",
    ),
]

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Pia", "Tess"]
BOY_NAMES = ["Eli", "Nico", "Finn", "Arlo", "Owen", "Jude"]
TRAITS = ["curious", "careful", "quiet", "brave", "patient", "bright"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A, P) :- uses(A, R), worn_on(P, R).

compatible(T, A, P) :- tool(T), prize_at_risk(A, P),
                       guards(T, M), mess_of(A, M),
                       covers(T, R), worn_on(P, R).

has_fix(A, P) :- compatible(_, A, P).

valid_story(Place, A, P, Gender) :- workshop(Place), affords(Place, A),
                                    prize_at_risk(A, P), has_fix(A, P),
                                    wears(Gender, P).

valid_combo(Place, A, P) :- workshop(Place), affords(Place, A),
                            prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = [asp.fact("workshop", "workshop")]
    for place, s in SETTINGS.items():
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", place, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        lines.append(asp.fact("uses", aid, "hands"))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p["region"]))
        lines.append(asp.fact("wears", "girl", pid))
        lines.append(asp.fact("wears", "boy", pid))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", t.id, g))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: dict) -> bool:
    return prize["region"] == "hands" or activity.id in {"glue", "paint", "wood"}


def select_tool(activity: Activity, prize: dict) -> Optional[Tool]:
    for t in TOOLS:
        if activity.mess in t.guards and prize["region"] in t.covers:
            return t
    return None


def explain_rejection(activity: Activity, prize: dict) -> str:
    return (
        f"(No story: {activity.gerund} would make trouble, but no tool in the workshop "
        f"both handles {activity.mess} and fits the {prize['label']}. Try a different prize.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for pid, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_tool(act, prize):
                    combos.append((place, act_id, pid))
    return combos


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters.get("dirty", 0) >= 1 or prize and prize.meters.get(activity.mess, 0) >= 1),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0) + 1
    world.say(f"{actor.id} worked on the bench, and the room answered with a faint {activity.sound}.")


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.memes.get('traits', [])), 'curious')} {hero.type} "
        f"who noticed every tiny clue in the workshop."
    )


def setup(world: World, hero: Entity, helper: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    helper.memes["bias"] = helper.memes.get("bias", 0) + 1
    world.say(
        f"Inside the workshop, {hero.id} loved solving little mysteries, while {helper.id} was sure "
        f"that the first sign of trouble was the whole answer."
    )
    world.say(f"{helper.id} had given {hero.pronoun('object')} {prize.phrase}, and {hero.id} kept it close.")
    world.say(
        f"Near the worktable, {activity.keyword} could get messy, and {activity.clue} looked like the kind of clue "
        f"that might matter later."
    )


def mystery_turn(world: World, hero: Entity, helper: Entity, activity: Activity, prize: Entity) -> None:
    world.para()
    world.say(
        f"One afternoon, {hero.id} heard a sharp {activity.sound} from the bench, and then saw {activity.clue}."
    )
    world.say(
        f"{hero.id} wanted to know who had been there. But {helper.id} guessed too fast and blamed the wrong tool."
    )
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    helper.memes["bias"] = helper.memes.get("bias", 0) + 1
    helper.memes["worry"] = helper.memes.get("worry", 0) + 1
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        world.say(
            f"{helper.id} frowned and warned that {prize.label} would get ruined if anyone kept going without a plan."
        )


def reconcile(world: World, hero: Entity, helper: Entity, activity: Activity, prize: Entity, tool: Tool) -> None:
    world.para()
    world.say(
        f"{hero.id} looked closer instead of guessing. The clue fit the {tool.label}, not the blamed tool, and the mistake became clear."
    )
    world.say(
        f"{hero.id} found the right fix: {tool.prep}, then {activity.verb}. That way the mess could be absorbed without ruining {prize.label}."
    )
    helper.memes["bias"] = max(0.0, helper.memes.get("bias", 0) - 1)
    helper.memes["reconciliation"] = helper.memes.get("reconciliation", 0) + 1
    hero.memes["reconciliation"] = hero.memes.get("reconciliation", 0) + 1
    helper.memes["relief"] = helper.memes.get("relief", 0) + 1
    world.say(
        f"{helper.id} apologized, and {hero.id} smiled. Together they {tool.tail}, and the workshop grew quiet again."
    )
    world.say(
        f"At the end, the clue was solved, the bias was gone, and {hero.id}'s {prize.label} stayed clean."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: dict, hero_name: str, hero_type: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        memes={"curiosity": 1.0, "traits": ["curious"]},
    ))
    helper = world.add(Entity(
        id="Casey",
        kind="character",
        type=helper_type,
        memes={"bias": 1.0},
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg["label"],
        label=prize_cfg["label"],
        phrase=prize_cfg["phrase"],
        owner=hero.id,
        caretaker=helper.id,
    ))

    setup(world, hero, helper, prize, activity)
    mystery_turn(world, hero, helper, activity)
    tool = select_tool(activity, prize_cfg)
    if tool is None:
        raise StoryError(explain_rejection(activity, prize_cfg))
    reconcile(world, hero, helper, activity, prize, tool)

    world.facts.update(hero=hero, helper=helper, prize=prize, activity=activity, tool=tool, setting=setting)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    activity = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short mystery for children set in a workshop where {hero.id} notices a clue and uses {activity.keyword} to solve it.',
        f"Tell a story about curiosity and reconciliation in the workshop, where a sharp {activity.sound} helps reveal the truth about {prize.label}.",
        f'Write a gentle mystery that includes the words "absorb," "bias," and "smack" in a workshop scene.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prize = f["prize"]
    activity = f["activity"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Where does the mystery happen?",
            answer=f"It happens in the workshop, where {hero.id} watches clues on the bench and near the worktable.",
        ),
        QAItem(
            question=f"Why did {helper.id} guess too fast?",
            answer=f"{helper.id} had bias and blamed the wrong tool before looking closely at the clue.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem with {tool.label}?",
            answer=(
                f"{hero.id} used {tool.label} to absorb the mess first, then finished the job carefully so {prize.label} stayed clean."
            ),
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=(
                f"The misunderstanding turned into reconciliation. {helper.id} apologized, {hero.id} was relieved, and the workshop became quiet again."
            ),
        ),
    ]


KNOWLEDGE = {
    "absorb": [
        (
            "What does it mean when a sponge absorbs water?",
            "It means the sponge soaks up the water and holds it inside itself.",
        )
    ],
    "bias": [
        (
            "What is bias?",
            "Bias is when someone decides too quickly and does not give each clue a fair look.",
        )
    ],
    "smack": [
        (
            "What can a smack sound mean in a workshop?",
            "A smack can be the sharp sound of a tool touching wood, a bench, or a container.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a puzzle or problem that needs careful looking and thinking to solve.",
        )
    ],
    "reconciliation": [
        (
            "What is reconciliation?",
            "Reconciliation is when people make up after a disagreement and feel friendly again.",
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the wish to look, ask, and learn what is really going on.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in ["absorb", "bias", "smack", "mystery", "reconciliation", "curiosity"]:
        if tag in tags or tag in {"mystery", "reconciliation", "curiosity"}:
            for q, a in KNOWLEDGE[tag]:
                out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameter resolution and generation
# ---------------------------------------------------------------------------
def valid_story_options() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for pid, prize in PRIZES.items():
                if prize_at_risk(ACTIVITIES[act], prize) and select_tool(ACTIVITIES[act], prize):
                    combos.append((place, act, pid))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_story_options()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or "friend"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.helper,
    )
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


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_story_options())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_story_options() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python.")
    print("Only in clingo:", sorted(cl - py))
    print("Only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="workshop", activity="glue", prize="notebook", name="Mina", gender="girl", helper="mentor", trait="curious"),
    StoryParams(place="workshop", activity="paint", prize="apron", name="Eli", gender="boy", helper="uncle", trait="careful"),
    StoryParams(place="workshop", activity="wood", prize="gloves", name="Nora", gender="girl", helper="aunt", trait="bright"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld set in a workshop.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait")
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        for x in asp_valid_combos():
            print(x)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.activity} in the workshop"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
