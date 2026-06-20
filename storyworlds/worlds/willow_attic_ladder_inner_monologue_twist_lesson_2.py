#!/usr/bin/env python3
"""
storyworlds/worlds/willow_attic_ladder_inner_monologue_twist_lesson_2.py
========================================================================

A small standalone storyworld for a pirate-flavored attic-ladder tale.

The source-tale premise behind this world is simple: a child playing pirate
hears a strange sound above an attic ladder, imagines treasure trouble, thinks
through the risk, climbs carefully with a fitting plan, and discovers that the
frightening sign came from a harmless willow basket. The twist matters because
it changes both what the hero believes and how the hero moves.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class LadderState:
    key: str
    phrase: str
    risk: str
    image: str
    allowed_plans: tuple[str, ...]
    risk_level: float


@dataclass(frozen=True)
class SignState:
    key: str
    apparent: str
    inner_monologue: str
    cause: str
    prize: str
    reveal: str
    ending_image: str
    lesson: str
    fear_gain: float


@dataclass(frozen=True)
class ClimbPlan:
    key: str
    phrase: str
    cue: str
    action: str
    physical_effect: str
    lesson_line: str
    stabilizes: tuple[str, ...]


@dataclass
class StoryParams:
    ladder: str
    sign: str
    plan: str
    hero: str
    gender: str
    helper: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"girl", "mother", "aunt", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind in {"boy", "father", "uncle", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Event:
    key: str
    details: dict[str, str]


@dataclass
class World:
    params: StoryParams
    ladder: LadderState
    sign: SignState
    plan: ClimbPlan
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)
    fired: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def event(self, key: str, **details: str) -> None:
        self.history.append(Event(key=key, details=details))
        self.fired.append(key)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        for name, ent in self.entities.items():
            traits = ", ".join(ent.traits) if ent.traits else "none"
            rows.append(
                f"  {name:<12} ({ent.kind:<10})"
                f" location={ent.location:<12} traits=[{traits}]"
                f" meters={dict(ent.meters)} memes={dict(ent.memes)}"
            )
        rows.append(f"  ladder: {self.ladder.key} ({self.ladder.phrase})")
        rows.append(f"  sign: {self.sign.key} ({self.sign.apparent})")
        rows.append(f"  plan: {self.plan.key} ({self.plan.phrase})")
        rows.append(f"  facts: {json.dumps(self.facts, sort_keys=True)}")
        rows.append(f"  events: {self.fired}")
        return "\n".join(rows)


LADDERS = {
    "dusty_rungs": LadderState(
        key="dusty_rungs",
        phrase="the pull-down attic ladder above the hall",
        risk="a powder of dust made the middle rungs slippery",
        image="The narrow ladder hung from the ceiling like a ship's gangplank in still air.",
        allowed_plans=("lantern_first", "steady_base"),
        risk_level=2.0,
    ),
    "wobbly_hinge": LadderState(
        key="wobbly_hinge",
        phrase="the attic ladder by the linen closet",
        risk="one hinge clicked and swayed whenever a foot pressed too fast",
        image="Each rung gave a small shiver, like a mast rope in a teasing wind.",
        allowed_plans=("steady_base", "test_each_rung"),
        risk_level=2.0,
    ),
    "steep_shadow": LadderState(
        key="steep_shadow",
        phrase="the attic ladder over the back stairs",
        risk="the top steps rose steeply into a pocket of shadow",
        image="The ladder climbed almost straight up, disappearing into the dim attic mouth.",
        allowed_plans=("lantern_first", "test_each_rung"),
        risk_level=2.0,
    ),
}

SIGNS = {
    "ghost_moan": SignState(
        key="ghost_moan",
        apparent="a ghost captain was moaning over hidden gold",
        inner_monologue='I am only a small deckhand, but a true pirate does not flee from a moan.',
        cause="night air was humming through the reeds of a willow basket",
        prize="a rolled play-map painted on old sail cloth",
        reveal="The long moan came from the basket itself, not from any ghost at all.",
        ending_image="The willow basket rested quietly at the attic lip while the sail-cloth map curled open on the floor below.",
        lesson="A spooky sound may be only a loose thing asking for a careful look.",
        fear_gain=1.4,
    ),
    "clawing_rat": SignState(
        key="clawing_rat",
        apparent="a sea rat was scratching beside the captain's prize",
        inner_monologue='If I tarry, that bold rat will claim the treasure before I do.',
        cause="a tin hook was tapping the side of a willow basket whenever the ladder shook",
        prize="a bright brass button compass from an old dress-up coat",
        reveal="The scratching was only tin against wicker, and the basket held treasure for pretending rather than stealing.",
        ending_image="The brass compass winked in the lantern glow while the tin hook lay still against the basket.",
        lesson="When feet rush, ordinary noise can grow into a monster inside the mind.",
        fear_gain=1.2,
    ),
    "captain_whisper": SignState(
        key="captain_whisper",
        apparent="an unseen captain was whispering secret orders from the dark",
        inner_monologue='What if the whisper means some old captain has chosen me for a secret voyage?',
        cause="a folded letter inside the willow basket was rustling against the wicker",
        prize="a note calling {hero} the captain of careful feet",
        reveal="The whisper belonged to paper and reeds, not to any hidden spirit.",
        ending_image="The note rested in the hero's hand, and the attic air felt soft instead of haunted.",
        lesson="The best treasure is advice that changes how you move through danger.",
        fear_gain=1.0,
    ),
}

PLANS = {
    "lantern_first": ClimbPlan(
        key="lantern_first",
        phrase="a blue-glass lantern",
        cue="light the way before taking the next step",
        action="{helper} lifted a blue-glass lantern so the ladder and attic mouth could be seen clearly.",
        physical_effect="The light showed where dust and shadow sat, and it made the next foothold honest.",
        lesson_line="A captain who wants treasure should begin by making the path plain.",
        stabilizes=("dusty_rungs", "steep_shadow"),
    ),
    "steady_base": ClimbPlan(
        key="steady_base",
        phrase="two steady hands at the ladder's foot",
        cue="steady the ship before boarding",
        action="{helper} planted both feet and gripped the ladder's sides so it would not sway.",
        physical_effect="The ladder stopped wagging, and the climb felt more like boarding a ship at dock than chasing one at sea.",
        lesson_line="Even brave climbing grows wiser when someone keeps the base secure.",
        stabilizes=("dusty_rungs", "wobbly_hinge"),
    ),
    "test_each_rung": ClimbPlan(
        key="test_each_rung",
        phrase="a slow tap on every rung",
        cue="test each board before trusting your weight to it",
        action="{hero} tapped each rung with careful toes and paused before rising higher.",
        physical_effect="The patient rhythm quieted the wobble and turned the climb into a measured boarding.",
        lesson_line="Speed is not the same as skill when the way up is narrow.",
        stabilizes=("wobbly_hinge", "steep_shadow"),
    ),
}

HEROES = {
    "girl": ("Mira", "Nell", "Sera", "Tilda"),
    "boy": ("Bram", "Ivo", "Nico", "Tobin"),
}

HELPERS = ("Aunt June", "Uncle Reed", "Mama", "Grandpa")


def valid_combo(ladder_key: str, sign_key: str, plan_key: str) -> bool:
    if ladder_key not in LADDERS or sign_key not in SIGNS or plan_key not in PLANS:
        return False
    ladder = LADDERS[ladder_key]
    plan = PLANS[plan_key]
    return plan_key in ladder.allowed_plans and ladder_key in plan.stabilizes


def invalid_reason(ladder_key: str, sign_key: str, plan_key: str) -> str:
    if ladder_key not in LADDERS:
        return f"No story: unknown ladder state {ladder_key!r}."
    if sign_key not in SIGNS:
        return f"No story: unknown attic sign {sign_key!r}."
    if plan_key not in PLANS:
        return f"No story: unknown climb plan {plan_key!r}."
    ladder = LADDERS[ladder_key]
    plan = PLANS[plan_key]
    if plan_key not in ladder.allowed_plans:
        return (
            f"No story: {ladder.phrase} does not fit plan {plan_key!r}. "
            f"Try one of: {', '.join(ladder.allowed_plans)}."
        )
    if ladder_key not in plan.stabilizes:
        return (
            f"No story: {plan.phrase} does not meaningfully stabilize {ladder_key!r}. "
            f"It stabilizes: {', '.join(plan.stabilizes)}."
        )
    return "No story: invalid combination."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for ladder_key in sorted(LADDERS):
        for sign_key in sorted(SIGNS):
            for plan_key in sorted(PLANS):
                if valid_combo(ladder_key, sign_key, plan_key):
                    combos.append((ladder_key, sign_key, plan_key))
    return combos


def _pick_hero(gender: str, rng: random.Random) -> str:
    return rng.choice(HEROES[gender])


def _helper_kind(name: str) -> str:
    if name.startswith("Aunt") or name == "Mama":
        return "mother"
    if name.startswith("Uncle") or name == "Grandpa":
        return "father"
    return "adult"


def _params_from_combo(args: argparse.Namespace, combo: tuple[str, str, str], index: int = 0) -> StoryParams:
    seed = (args.seed or 1) + index
    rng = random.Random(seed)
    gender = args.gender or rng.choice(sorted(HEROES))
    hero = args.hero or _pick_hero(gender, rng)
    helper = args.helper or rng.choice(HELPERS)
    ladder_key, sign_key, plan_key = combo
    return StoryParams(
        ladder=ladder_key,
        sign=sign_key,
        plan=plan_key,
        hero=hero,
        gender=gender,
        helper=helper,
        seed=seed,
    )


def build_world(params: StoryParams) -> World:
    ladder = LADDERS[params.ladder]
    sign = SIGNS[params.sign]
    plan = PLANS[params.plan]
    world = World(params=params, ladder=ladder, sign=sign, plan=plan)

    hero = world.add(
        Entity(
            id=params.hero,
            kind=params.gender,
            label="deckhand child",
            location="hall",
            traits=["curious", "imaginative"],
        )
    )
    helper = world.add(
        Entity(
            id=params.helper,
            kind=_helper_kind(params.helper),
            label="steady helper",
            location="hall",
            traits=["calm", "watchful"],
        )
    )
    ladder_ent = world.add(
        Entity(
            id="ladder",
            kind="object",
            label="attic ladder",
            location="hall ceiling",
            traits=["wooden", "narrow"],
        )
    )
    basket = world.add(
        Entity(
            id="basket",
            kind="object",
            label="willow basket",
            location="attic lip",
            traits=["woven", "light"],
        )
    )
    prize = world.add(
        Entity(
            id="prize",
            kind="object",
            label="attic treasure",
            location="basket",
            traits=["hidden"],
        )
    )

    hero.memes["wonder"] = 1.2
    hero.memes["care"] = 0.8
    hero.memes["fear"] = 0.0
    hero.memes["relief"] = 0.0
    hero.meters["height"] = 1.2

    helper.memes["care"] = 1.5
    helper.meters["height"] = 1.7

    ladder_ent.meters["risk"] = ladder.risk_level
    ladder_ent.meters["stable"] = 0.0
    basket.meters["sway"] = 1.0
    basket.meters["opened"] = 0.0
    prize.meters["found"] = 0.0

    world.facts["setting"] = "attic ladder"
    world.facts["style"] = "pirate tale"
    world.facts["seed_word"] = "willow"
    world.facts["apparent_sign"] = sign.apparent
    world.facts["true_cause"] = sign.cause
    world.facts["prize"] = sign.prize.format(hero=params.hero)
    world.facts["helper"] = params.helper
    world.facts["hero"] = params.hero
    world.facts["plan_cue"] = plan.cue
    world.facts["lesson"] = ""
    return world


def simulate(world: World) -> None:
    hero = world.entities[world.params.hero]
    helper = world.entities[world.params.helper]
    ladder = world.entities["ladder"]
    basket = world.entities["basket"]
    prize = world.entities["prize"]
    sign = world.sign
    plan = world.plan

    hero.memes["fear"] += sign.fear_gain
    world.event("notice_sign", place=world.ladder.phrase, apparent=sign.apparent)

    hero.memes["reflection"] += 1.0
    world.event("inner_monologue", thought=sign.inner_monologue)

    ladder.meters["stable"] += 2.3
    hero.memes["care"] += 0.9
    helper.memes["care"] += 0.3
    world.event("make_plan", action=plan.action.format(helper=helper.id, hero=hero.id), cue=plan.cue)

    if ladder.meters["stable"] < ladder.meters["risk"]:
        raise StoryError("No story: the ladder never becomes safe enough to climb.")

    hero.location = "attic ladder"
    ladder.meters["risk"] = max(0.0, ladder.meters["risk"] - 1.1)
    world.event("climb", effect=plan.physical_effect)

    basket.meters["opened"] = 1.0
    basket.meters["sway"] = 0.0
    prize.meters["found"] = 1.0
    hero.location = "attic lip"
    world.event("reveal_twist", reveal=sign.reveal, cause=sign.cause, prize=world.facts["prize"])

    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 0.8)
    hero.memes["relief"] += 1.4
    hero.memes["prudence"] += 1.3
    world.facts["lesson"] = f"{plan.lesson_line} {sign.lesson}"
    world.event("lesson_learned", lesson=world.facts["lesson"], ending=sign.ending_image)


def _render_story(world: World) -> str:
    hero = world.entities[world.params.hero]
    helper = world.entities[world.params.helper]
    opening = (
        f"One dusky evening, {hero.id} played deckhand beneath {world.ladder.phrase}. "
        f"{world.ladder.image} At the top, a willow basket rocked near the attic mouth."
    )
    tension = (
        f"Then a sound drifted down, and {hero.id} decided that {world.sign.apparent}. "
        f"{world.ladder.risk.capitalize()}."
    )
    inner = f'{hero.id} thought, "{world.sign.inner_monologue}"'
    plan = (
        f"Instead of charging upward like a foolish raider, {world.plan.action.format(helper=helper.id, hero=hero.id)} "
        f"{world.plan.physical_effect}"
    )
    climb = (
        f"With one hand on the rail and pirate care in {hero.pronoun('possessive')} chest, {hero.id} climbed toward the basket."
    )
    twist = (
        f"When {hero.pronoun('subject')} reached the top, the twist showed itself at once. "
        f"{world.sign.reveal} The true cause was simple: {world.sign.cause}, and inside waited {world.facts['prize']}."
    )
    ending = (
        f'{world.facts["lesson"]} {world.sign.ending_image} '
        f"{hero.id} grinned, for the best captains in any house learn to slow down before they seize a prize."
    )
    return "\n\n".join([opening, tension, inner, plan, climb, twist, ending])


def _prompts(world: World) -> list[str]:
    return [
        'Write a Pirate Tale set on an attic ladder and make sure the word "willow" appears in the story.',
        "Include an inner monologue, a twist about the scary sign, and a lesson learned at the end.",
        f"Let {world.params.hero} solve the problem with {world.plan.cue} instead of a reckless rush.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    hero = world.params.hero
    sign = world.sign
    plan = world.plan
    ladder = world.ladder
    return [
        QAItem(
            "What problem did the hero think was waiting above the ladder?",
            f"{hero} believed that {sign.apparent}. That belief came before the climb, so the danger first lived in imagination and only later got checked against the real attic.",
        ),
        QAItem(
            "What does the inner monologue show about the hero?",
            f'The thought "{sign.inner_monologue}" shows that {hero} wants to be brave in a pirate way. It also shows that bravery alone is tempting, which is why the later careful choice matters.',
        ),
        QAItem(
            "How was the climb made safer?",
            f"The climb became safer when the plan used {plan.phrase}. That choice fit the ladder because {ladder.risk}, so the hero changed the world before trying to win the prize.",
        ),
        QAItem(
            "What was the twist in the attic?",
            f"The frightening sign was not a real ghost or rat at all. {sign.reveal} The attic changed from a place of imagined danger into a place of ordinary causes and a harmless treasure.",
        ),
        QAItem(
            "What lesson did the hero learn?",
            f'{world.facts["lesson"]} By the end, {hero} understands that a careful captain earns treasure by reading the situation first, not by rushing at the first exciting sound.',
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why does this world track both meters and memes?",
            "The meters hold physical conditions like ladder stability, basket sway, and whether the prize was found. The memes hold feelings and habits like fear, care, relief, and prudence, so the lesson grows from state instead of from a pasted moral line.",
        ),
        QAItem(
            "Why is the willow basket important to the twist?",
            "The willow basket is the carrier that makes the strange sound in a grounded way. Because the reeds, hook, or letter belong to the basket, the reveal turns an eerie sign into a physical explanation inside the world.",
        ),
        QAItem(
            "Why are only some climb plans valid for each ladder?",
            "Each ladder state has a different physical problem, so the plan has to answer that exact problem. A story where any plan solved any ladder would weaken both the tension and the lesson about careful action.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.ladder, params.sign, params.plan):
        raise StoryError(invalid_reason(params.ladder, params.sign, params.plan))
    world = build_world(params)
    simulate(world)
    return StorySample(
        params=params,
        story=_render_story(world),
        prompts=_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


ASP_RULES = r"""
combo(L,S,P) :-
    ladder(L),
    sign(S),
    plan(P),
    allows(L,P),
    stabilizes(P,L),
    twist(S,_,_).

ok :- chosen(L,S,P), combo(L,S,P).

#show combo/3.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for ladder_key, ladder in sorted(LADDERS.items()):
        rows.append(fact("ladder", ladder_key))
        for plan_key in ladder.allowed_plans:
            rows.append(fact("allows", ladder_key, plan_key))
    for sign_key, sign in sorted(SIGNS.items()):
        rows.append(fact("sign", sign_key))
        rows.append(fact("twist", sign_key, sign.cause, sign.prize))
    for plan_key, plan in sorted(PLANS.items()):
        rows.append(fact("plan", plan_key))
        for ladder_key in plan.stabilizes:
            rows.append(fact("stabilizes", plan_key, ladder_key))
    if params is not None:
        rows.append(fact("chosen", params.ladder, params.sign, params.plan))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str]]:
    from storyworlds.asp import atoms, solve

    combos: set[tuple[str, str, str]] = set()
    for model in solve(asp_program(), models=0):
        combos.update(atoms(model, "combo"))
    return combos


def asp_verify(params: StoryParams) -> bool:
    from storyworlds.asp import atoms, one_model

    return bool(atoms(one_model(asp_program(params)), "ok"))


def verify() -> str:
    py = set(valid_combos())
    asp = asp_valid_combos()
    if py != asp:
        only_py = sorted(py - asp)
        only_asp = sorted(asp - py)
        raise StoryError(f"ASP/Python mismatch. only_python={only_py} only_asp={only_asp}")
    for index, combo in enumerate(sorted(py)):
        params = StoryParams(
            ladder=combo[0],
            sign=combo[1],
            plan=combo[2],
            hero="Mira",
            gender="girl",
            helper="Aunt June",
            seed=index + 1,
        )
        if not asp_verify(params):
            raise StoryError(f"ASP rejected valid combo {combo!r}.")
        sample = generate(params)
        if "willow" not in sample.story.lower():
            raise StoryError(f"Generated story omitted seed word for combo {combo!r}.")
        if "attic ladder" not in sample.story.lower():
            raise StoryError(f"Generated story omitted setting phrase for combo {combo!r}.")
        if not sample.story_qa or not sample.world_qa or not sample.prompts:
            raise StoryError(f"Generated story omitted QA/prompts for combo {combo!r}.")
    return f"OK: clingo gate matches valid_combos() and exercised {len(py)} stories."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate attic-ladder pirate tale storyworld samples.")
    parser.add_argument("--ladder", choices=sorted(LADDERS))
    parser.add_argument("--sign", choices=sorted(SIGNS))
    parser.add_argument("--plan", choices=sorted(PLANS))
    parser.add_argument("--hero", default=None)
    parser.add_argument("--gender", choices=sorted(HEROES), default=None)
    parser.add_argument("--helper", choices=HELPERS, default=None)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, index: int = 0) -> StoryParams:
    rng = random.Random((args.seed or 1) + index)
    combos = valid_combos()
    if args.ladder or args.sign or args.plan:
        combos = [
            combo
            for combo in combos
            if (args.ladder is None or combo[0] == args.ladder)
            and (args.sign is None or combo[1] == args.sign)
            and (args.plan is None or combo[2] == args.plan)
        ]
        if not combos:
            raise StoryError(
                invalid_reason(
                    args.ladder or "<ladder>",
                    args.sign or "<sign>",
                    args.plan or "<plan>",
                )
            )
    combo = rng.choice(combos)
    return _params_from_combo(args, combo, index)


def _print_qa(sample: StorySample) -> None:
    print("\n== (1) Story prompts ==")
    for i, prompt in enumerate(sample.prompts, 1):
        print(f"{i}. {prompt}")
    print("\n== (2) Story Q&A ==")
    for qa in sample.story_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")
    print("\n== (3) World Q&A ==")
    for qa in sample.world_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")


def emit(sample: StorySample, args: argparse.Namespace, label: str | None = None) -> None:
    if args.json:
        print(sample.to_json())
        return
    if label:
        print(label)
    print(sample.story)
    if args.trace and sample.world is not None:
        print(sample.world.trace())
    if args.qa:
        _print_qa(sample)


def _emit_asp_listing() -> None:
    for ladder_key, sign_key, plan_key in sorted(asp_valid_combos()):
        print(f"{ladder_key}\t{sign_key}\t{plan_key}")


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            _emit_asp_listing()
            return 0
        if args.all:
            combos = valid_combos()
            for i, combo in enumerate(combos, 1):
                sample = generate(_params_from_combo(args, combo, i))
                emit(sample, args, f"### {combo[0]} / {combo[1]} / {combo[2]}")
                if i != len(combos) and not args.json:
                    print("\n" + "=" * 72 + "\n")
            return 0
        count = max(1, args.n)
        for i in range(count):
            sample = generate(resolve_params(args, i))
            emit(sample, args, f"### variant {i + 1}" if count > 1 and not args.json else None)
            if i != count - 1 and not args.json:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
