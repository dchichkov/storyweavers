#!/usr/bin/env python3
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
    location: str = ""
    portable: bool = True
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the swimming pool"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    risk: str
    clue: str
    danger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    gender: str
    detective: str
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _narrate_jam_spill(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters.get("sticky", 0.0) < THRESHOLD:
            continue
        sig = ("spill", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if e.location in {"deck", "lanes", "pump_room"}:
            out.append(f"The jam made the floor slick and left a bright stain behind.")
            world.facts["jam_spill"] = True
    return out


def _narrate_alarm(world: World) -> list[str]:
    if not world.facts.get("jam_spill"):
        return []
    if ("alarm",) in world.fired:
        return []
    world.fired.add(("alarm",))
    return ["The caution sign by the pool could not be ignored." ]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_narrate_jam_spill, _narrate_alarm):
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    return "The swimming pool gleamed in the sun, and the deck was wet with little footprints."


def suspect_line(hero: Entity, detective: Entity, action: Action) -> str:
    return (
        f"{hero.id} had wanted to {action.verb}, but {detective.pronoun('possessive')} "
        f"eyes kept finding one clue after another."
    )


def predict(world: World, actor: Entity, action: Action) -> bool:
    sim = world.copy()
    _do_action(sim, sim.get(actor.id), action, narrate=False)
    return bool(sim.facts.get("jam_spill"))


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    actor.meters["sticky"] = actor.meters.get("sticky", 0.0) + 1
    world.facts["action_taken"] = action.id
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, detective: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a curious {hero.type} who noticed tiny things others missed."
    )
    world.say(
        f"One day, {hero.id} and {detective.pronoun('possessive')} {detective.type} came to "
        f"{world.setting.place} where {hero.pronoun('possessive')} {prize.label} was waiting."
    )


def clue_setup(world: World, hero: Entity, detective: Entity, action: Action, prize: Entity) -> None:
    world.say(
        f"{hero.id} liked to {action.verb}, and {action.gerund} always seemed to lead to a mystery."
    )
    world.say(
        f"Near the water, the only clue was a sticky little mark that matched {action.clue}."
    )


def warning(world: World, hero: Entity, detective: Entity, action: Action, prize: Entity) -> bool:
    if not predict(world, hero, action):
        return False
    world.facts["warned"] = True
    world.say(
        f'"If you do that now, the {prize.label} will get {action.danger}," '
        f"{detective.id} warned. \"That would be a bad surprise.\""
    )
    return True


def resolve(world: World, hero: Entity, detective: Entity, action: Action, prize: Prize) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    world.say(
        f"{hero.id} stopped, looked at the slippery deck, and chose the safer path instead."
    )
    world.say(
        f"{hero.id} used a dry towel to carry the {prize.label} away from the water, "
        f"and the odd stain finally made sense."
    )
    world.say(
        f"In the end, the clue was not a trick at all: it was a warning that kept everyone safe."
    )
    world.facts["resolved"] = True


def tell(setting: Setting, action: Action, prize: Prize, hero_name: str, hero_type: str,
         detective_type: str = "father") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    detective = world.add(Entity(id="Detective", kind="character", type=detective_type))
    kept_item = world.add(Entity(
        id="Prize", type=prize.type, label=prize.label, phrase=prize.phrase,
        owner=hero.id, caretaker=detective.id, location=prize.location, plural=prize.plural
    ))

    intro(world, hero, detective, kept_item)
    world.para()
    world.say(setting_detail(setting))
    clue_setup(world, hero, detective, action, kept_item)
    warning(world, hero, detective, action, kept_item)
    world.para()
    world.say(suspect_line(hero, detective, action))
    resolve(world, hero, detective, action, prize)

    world.facts.update(hero=hero, detective=detective, prize=kept_item, action=action, setting=setting)
    return world


SETTINGS = {
    "swimming_pool": Setting(place="the swimming pool", affords={"buy", "jam"}),
}

ACTIONS = {
    "buy": Action(
        id="buy",
        verb="buy the old estate by the pool",
        gerund="buying the old estate by the pool",
        risk="too many questions",
        clue="a receipt from the estate office",
        danger="wet and ruined papers",
        tags={"buy", "estate"},
    ),
    "jam": Action(
        id="jam",
        verb="open the jam jar by the water",
        gerund="opening the jam jar by the water",
        risk="a sticky spill",
        clue="a red smear on the deck",
        danger="sticky and slippery marks",
        tags={"jam"},
    ),
}

PRIZES = {
    "estate": Prize(
        label="estate papers",
        phrase="the estate papers",
        type="papers",
        location="deck",
        plural=True,
    ),
    "jam": Prize(
        label="jam jar",
        phrase="a jar of strawberry jam",
        type="jar",
        location="deck",
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Tara", "Iris", "Nora"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Theo", "Milo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                combos.append((place, act_id, prize_id))
    return combos


def explain_rejection() -> str:
    return "(No story: that combination does not fit the swimming-pool whodunit.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary whodunit at a swimming pool.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--detective", choices=["mother", "father"])
    ap.add_argument("--name")
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
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError(explain_rejection())
    place, action, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    detective = args.detective or rng.choice(["mother", "father"])
    return StoryParams(place=place, action=action, prize=prize, name=name, gender=gender, detective=detective)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a cautionary whodunit for a child at {f["setting"].place} that includes the word "buy".',
        f'Write a mystery story where {f["hero"].id} notices a clue, worries about a jam stain, and learns why caution matters.',
        f'Tell a short whodunit set at a swimming pool with an old estate purchase and a sticky jam clue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    detective: Entity = f["detective"]
    prize: Entity = f["prize"]
    action: Action = f["action"]
    qa = [
        QAItem(
            question=f"What was {hero.id} trying to do near the swimming pool?",
            answer=f"{hero.id} was trying to {action.verb}, but that led to a mystery clue instead of a simple day of fun.",
        ),
        QAItem(
            question=f"Why did {detective.id} warn {hero.id} about the {prize.label}?",
            answer=f"{detective.id} warned {hero.id} because the action could leave the {prize.label} sticky and ruined.",
        ),
        QAItem(
            question="What solved the mystery in the end?",
            answer="The sticky mark on the deck showed that the danger was real, so the child stopped and chose the safer way.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did {hero.id} stay safe at the swimming pool?",
            answer=f"{hero.id} stopped before the mistake, moved the {prize.label} away from the water, and listened to the warning.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an estate?",
            answer="An estate is a large property or piece of land, sometimes with a big house on it.",
        ),
        QAItem(
            question="What is jam?",
            answer="Jam is a sweet fruit spread that can be sticky if it spills.",
        ),
        QAItem(
            question="Why should people be careful around a swimming pool?",
            answer="People should be careful around a swimming pool because wet ground can be slippery and unsafe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A,R) :- place(P), action(A), prize(R), affords(P,A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for rid in PRIZES:
        lines.append(asp.fact("prize", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show valid/3."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    if asp_set - py_set:
        print("only in asp:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("only in python:", sorted(py_set - asp_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIONS[params.action],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.detective,
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as e:
            raise SystemExit(f"ASP unavailable: {e}")
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:")
        for v in vals:
            print(v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in [
            StoryParams("swimming_pool", "buy", "estate", "Mina", "girl", "mother"),
            StoryParams("swimming_pool", "jam", "jam", "Eli", "boy", "father"),
        ]:
            samples.append(generate(p))
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
