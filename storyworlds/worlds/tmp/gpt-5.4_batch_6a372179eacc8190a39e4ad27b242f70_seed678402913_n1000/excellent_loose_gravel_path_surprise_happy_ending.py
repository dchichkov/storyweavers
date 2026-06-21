#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/excellent_loose_gravel_path_surprise_happy_ending.py
================================================================================

A small storyworld for a folk-tale-style bravery story set on a loose gravel
path. A child traveler hears trouble ahead, faces a risky slope, chooses a
sensible rescue aid, and earns a surprising happy ending.

The world is intentionally narrow and constraint-checked:

- The setting is always a loose gravel path, where slipping is a real risk.
- A rescue problem may require steady footing, extra reach, or pulling power.
- An aid is only accepted when it honestly matches the need.
- The story always includes bravery, a surprise, and a happy ending.
- The word "excellent" appears naturally in the prose.

Run it
------
    python storyworlds/worlds/gpt-5.4/excellent_loose_gravel_path_surprise_happy_ending.py
    python storyworlds/worlds/gpt-5.4/excellent_loose_gravel_path_surprise_happy_ending.py --problem lamb_gully --aid rope
    python storyworlds/worlds/gpt-5.4/excellent_loose_gravel_path_surprise_happy_ending.py --problem sparrow_thorn
    python storyworlds/worlds/gpt-5.4/excellent_loose_gravel_path_surprise_happy_ending.py --all
    python storyworlds/worlds/gpt-5.4/excellent_loose_gravel_path_surprise_happy_ending.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/excellent_loose_gravel_path_surprise_happy_ending.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandmother", "grandfather": "grandfather"}.get(self.type, self.type)


@dataclass
class Problem:
    id: str
    creature: str
    creature_phrase: str
    peril: str
    place_detail: str
    call_sound: str
    need_stable: bool
    need_reach: bool
    need_pull: bool
    risk_text: str
    rescue_text: str
    after_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    stable: bool
    reach: bool
    pull: bool
    use_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    giver: str
    approach: str
    gift: str
    reveal_text: str
    blessing_text: str
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_scare(world: World) -> list[str]:
    hero = world.get("hero")
    path = world.get("path")
    trouble = world.get("trouble")
    if trouble.meters["in_peril"] < THRESHOLD:
        return []
    sig = ("scare", "peril")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["concern"] += 1
    hero.memes["bravery"] += 1
    path.meters["danger"] += 1
    return ["__peril__"]


def _r_resolve(world: World) -> list[str]:
    trouble = world.get("trouble")
    hero = world.get("hero")
    if trouble.meters["safe"] < THRESHOLD:
        return []
    sig = ("resolve", "safe")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    return ["__safe__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="scare", tag="emotion", apply=_r_scare),
    Rule(name="resolve", tag="emotion", apply=_r_resolve),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


PROBLEMS = {
    "lamb_gully": Problem(
        id="lamb_gully",
        creature="lamb",
        creature_phrase="a white lamb",
        peril="slid into a shallow gully below the path",
        place_detail="where the loose gravel path bent around a dusty hill",
        call_sound="a thin baa-baa",
        need_stable=True,
        need_reach=True,
        need_pull=True,
        risk_text="Each step sent pebbles skittering underfoot, and one bad slip could send the rescuer sliding too.",
        rescue_text="The lamb scrabbled with its little hooves, but the stones rolled away under it.",
        after_text="Once it stood on the path again, it pressed its warm nose against the child's hand.",
        tags={"lamb", "animal", "gravel", "rescue"},
    ),
    "sparrow_thorn": Problem(
        id="sparrow_thorn",
        creature="sparrow",
        creature_phrase="a small brown sparrow",
        peril="fluttered low with one wing caught in a thorny briar beside the path",
        place_detail="where the loose gravel path narrowed between bramble bushes",
        call_sound="a frightened chirp-chirp",
        need_stable=True,
        need_reach=True,
        need_pull=False,
        risk_text="The gravel slipped toward the briars, and the thorns waited close to the child's knees.",
        rescue_text="The little bird beat its free wing in a blur and only tangled itself more.",
        after_text="When it was free, it hopped to a stone, shook itself, and sprang into the air.",
        tags={"sparrow", "bird", "thorn", "rescue"},
    ),
    "cart_wheel": Problem(
        id="cart_wheel",
        creature="cart",
        creature_phrase="a berry cart",
        peril="tilted with one wheel sunk between stones at the edge of the path",
        place_detail="where the loose gravel path climbed toward a little rise",
        call_sound="the creak-creak of wood and a worried sigh",
        need_stable=True,
        need_reach=False,
        need_pull=True,
        risk_text="Loose stones ran under every shoe, and the cart could tip farther if pushed the wrong way.",
        rescue_text="Red berries trembled in their basket, almost ready to spill into the gravel.",
        after_text="When the wheel rose free, the cart settled straight and the berries stopped shaking.",
        tags={"cart", "berries", "gravel", "help"},
    ),
}

AIDS = {
    "rope": Aid(
        id="rope",
        label="rope",
        phrase="a coil of rope",
        stable=True,
        reach=True,
        pull=True,
        use_text="braced steady feet on the gravel, lowered the rope with patient hands, and pulled at just the right moment",
        qa_text="used a rope to reach safely and pull the trouble back to the path",
        tags={"rope", "tool", "rescue"},
    ),
    "walking_stick": Aid(
        id="walking_stick",
        label="walking stick",
        phrase="a smooth walking stick",
        stable=True,
        reach=True,
        pull=False,
        use_text="planted the walking stick deep among the stones and used it to steady the careful rescue",
        qa_text="used a walking stick to keep steady on the loose gravel and reach carefully",
        tags={"stick", "tool", "balance"},
    ),
    "strap": Aid(
        id="strap",
        label="leather strap",
        phrase="a leather strap from the satchel",
        stable=False,
        reach=True,
        pull=True,
        use_text="swung the leather strap down in one quick brave try",
        qa_text="used a leather strap to reach down and tug",
        tags={"strap", "tool"},
    ),
    "hands": Aid(
        id="hands",
        label="bare hands",
        phrase="bare hands alone",
        stable=False,
        reach=False,
        pull=False,
        use_text="scrambled down with bare hands alone",
        qa_text="tried to do the job with bare hands alone",
        tags={"hands"},
    ),
}

SURPRISES = {
    "orchard_keeper": Surprise(
        id="orchard_keeper",
        giver="an orchard keeper",
        approach="an old orchard keeper stepped from behind a pear tree gate",
        gift="a small basket of honey pears",
        reveal_text='The old keeper laughed softly and said, "That lamb is mine, and your brave heart has done an excellent deed."',
        blessing_text="The pears were golden and sweet, and the child carried them home as if carrying sunlight.",
        tags={"pears", "gift", "surprise"},
    ),
    "hidden_fiddler": Surprise(
        id="hidden_fiddler",
        giver="a traveling fiddler",
        approach="a traveling fiddler appeared from behind the hill with a bright grin",
        gift="a silver bell on a blue ribbon",
        reveal_text='The fiddler bowed and said, "I saw all of it, and that was excellent courage on a hard path."',
        blessing_text="The little bell sang with every step, and even the gravel seemed to ring with good luck.",
        tags={"bell", "gift", "surprise"},
    ),
    "miller": Surprise(
        id="miller",
        giver="the miller from the valley",
        approach="the miller from the valley came hurrying up with flour still on his sleeves",
        gift="a warm round loaf wrapped in clean cloth",
        reveal_text='The miller smiled wide and said, "You saved my cart, and that was an excellent help indeed."',
        blessing_text="The loaf smelled of warm grain, and the child's whole house felt richer when evening came.",
        tags={"bread", "gift", "surprise"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Elsie", "Nora", "Willa", "Ada", "Rosa"]
BOY_NAMES = ["Tobin", "Milo", "Ivo", "Perrin", "Oren", "Hale", "Rowan", "Ned"]
TRAITS = ["kind", "careful", "steady", "bright", "gentle", "thoughtful"]


def aid_fits(problem: Problem, aid: Aid) -> bool:
    if problem.need_stable and not aid.stable:
        return False
    if problem.need_reach and not aid.reach:
        return False
    if problem.need_pull and not aid.pull:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for pid, problem in PROBLEMS.items():
        for aid_id, aid in AIDS.items():
            if aid_fits(problem, aid):
                for sid in SURPRISES:
                    combos.append((pid, aid_id, sid))
    return combos


def explain_rejection(problem: Problem, aid: Aid) -> str:
    reasons: list[str] = []
    if problem.need_stable and not aid.stable:
        reasons.append("the loose gravel path needs a way to keep steady")
    if problem.need_reach and not aid.reach:
        reasons.append("the trouble is too far down or too tucked away to reach")
    if problem.need_pull and not aid.pull:
        reasons.append("the rescue needs pulling strength as well as courage")
    joined = "; ".join(reasons) if reasons else "the aid does not truly match the rescue"
    return f"(No story: {aid.label} is not a sensible fix here because {joined}.)"


def predict_rescue(world: World, problem: Problem, aid: Aid) -> dict:
    sim = world.copy()
    if aid_fits(problem, aid):
        sim.get("trouble").meters["safe"] += 1
    propagate(sim, narrate=False)
    return {
        "success": sim.get("trouble").meters["safe"] >= THRESHOLD,
        "danger": sim.get("path").meters["danger"],
    }


def open_tale(world: World, hero: Entity) -> None:
    world.say(
        f"In the days when stories still seemed to hide behind hedges and hills, "
        f"there lived {hero.id}, a {next(iter([t for t in hero.traits if t != 'little']), 'kind')} "
        f"little {hero.type} who never hurried past a troubled sound."
    )
    world.say(
        "One clear morning, "
        f"{hero.pronoun()} walked along a loose gravel path with a satchel, a brave heart, "
        "and more curiosity than breakfast."
    )


def path_scene(world: World, problem: Problem) -> None:
    world.say(
        f"The path was pale and whispery underfoot, and it wound {problem.place_detail}. "
        f"Now and then the stones slid with a dry hiss."
    )
    world.say(
        f"Then {world.get('hero').id} heard {problem.call_sound}, small but sharp enough to stop the day."
    )


def discover_trouble(world: World, problem: Problem) -> None:
    trouble = world.get("trouble")
    trouble.meters["in_peril"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Just beyond the bend, {problem.creature_phrase} {problem.peril}. "
        f"{problem.rescue_text}"
    )
    world.say(problem.risk_text)


def choose_aid(world: World, hero: Entity, problem: Problem, aid: Aid) -> None:
    pred = predict_rescue(world, problem, aid)
    world.facts["predicted_danger"] = pred["danger"]
    hero.memes["resolve"] += 1
    world.say(
        f"{hero.id} did not run away and did not shout for luck to do the work. "
        f"{hero.pronoun().capitalize()} took {aid.phrase} and studied the stones."
    )
    world.say(
        f'"Slow feet and steady hands," {hero.pronoun()} whispered. '
        f'"That is the way on a loose gravel path."'
    )


def rescue(world: World, hero: Entity, problem: Problem, aid: Aid) -> None:
    world.get("trouble").meters["safe"] += 1
    propagate(world, narrate=False)
    hero.memes["bravery"] += 1
    hero.meters["helped"] += 1
    world.say(
        f"Then {hero.pronoun()} {aid.use_text}. Pebbles pattered downhill, "
        f"but {hero.pronoun('possessive')} courage held fast."
    )
    world.say(
        f"In another breath the trouble was over. {problem.after_text}"
    )


def surprise_ending(world: World, hero: Entity, surprise: Surprise, problem: Problem) -> None:
    world.para()
    world.say(
        f"But the tale was not finished, for a surprise was walking toward {hero.pronoun('object')} all the while."
    )
    world.say(
        f"From the far side of the bend, {surprise.approach}. "
        f"{surprise.reveal_text}"
    )
    world.say(
        f"As thanks, {surprise.giver} gave {hero.id} {surprise.gift}. "
        f"{surprise.blessing_text}"
    )
    world.say(
        f"And so {hero.id} went home by the same loose gravel path, no richer in coins perhaps, "
        f"but richer in courage, kindness, and a happy memory that lasted longer than dust."
    )
    world.facts["happy_image"] = surprise.gift
    world.facts["surprise_seen"] = True


def tell(
    problem: Problem,
    aid: Aid,
    surprise: Surprise,
    *,
    name: str = "Lina",
    gender: str = "girl",
    trait: str = "kind",
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=gender,
        label=name,
        phrase=name,
        traits=["little", trait],
        role="hero",
        tags={"child"},
    ))
    hero.attrs["name"] = name
    path = world.add(Entity(
        id="path",
        type="path",
        label="loose gravel path",
        phrase="the loose gravel path",
        tags={"path", "gravel"},
    ))
    trouble = world.add(Entity(
        id="trouble",
        type=problem.creature,
        label=problem.creature,
        phrase=problem.creature_phrase,
        role="trouble",
        tags=set(problem.tags),
    ))

    open_tale(world, hero)
    path_scene(world, problem)

    world.para()
    discover_trouble(world, problem)
    choose_aid(world, hero, problem, aid)
    rescue(world, hero, problem, aid)

    surprise_ending(world, hero, surprise, problem)

    world.facts.update(
        hero=hero,
        hero_name=name,
        path=path,
        trouble=trouble,
        problem=problem,
        aid=aid,
        surprise=surprise,
        brave=hero.memes["bravery"] >= THRESHOLD,
        success=trouble.meters["safe"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    problem: str
    aid: str
    surprise: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        problem="lamb_gully",
        aid="rope",
        surprise="orchard_keeper",
        name="Lina",
        gender="girl",
        trait="kind",
    ),
    StoryParams(
        problem="sparrow_thorn",
        aid="walking_stick",
        surprise="hidden_fiddler",
        name="Tobin",
        gender="boy",
        trait="careful",
    ),
    StoryParams(
        problem="cart_wheel",
        aid="rope",
        surprise="miller",
        name="Mira",
        gender="girl",
        trait="steady",
    ),
    StoryParams(
        problem="cart_wheel",
        aid="rope",
        surprise="hidden_fiddler",
        name="Oren",
        gender="boy",
        trait="bright",
    ),
]


KNOWLEDGE = {
    "gravel": [
        (
            "What is gravel?",
            "Gravel is a lot of small loose stones. It rolls under feet more easily than firm ground.",
        )
    ],
    "rope": [
        (
            "Why is a rope useful in a rescue?",
            "A rope lets you reach from a safer place and pull gently without climbing too close to danger.",
        )
    ],
    "stick": [
        (
            "What can a walking stick help with?",
            "A walking stick can help you keep your balance on rough ground and reach a little farther without leaning too much.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing a hard helpful thing even when you feel afraid. It is not rushing foolishly; it is choosing the good thing carefully.",
        )
    ],
    "surprise": [
        (
            "What is a surprise in a story?",
            "A surprise is something unexpected that happens after you think you know what comes next. It can make the ending feel bright and memorable.",
        )
    ],
    "lamb": [
        (
            "What is a lamb?",
            "A lamb is a young sheep. Lambs are small and can need help if they slip or get stuck.",
        )
    ],
    "sparrow": [
        (
            "What is a sparrow?",
            "A sparrow is a small bird. Small birds can get hurt easily if wings or feet are caught.",
        )
    ],
    "cart": [
        (
            "What is a cart?",
            "A cart is a small wagon used to carry things. If one wheel sinks or sticks, the cart can tip over.",
        )
    ],
}
KNOWLEDGE_ORDER = ["gravel", "rope", "stick", "bravery", "surprise", "lamb", "sparrow", "cart"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    aid = f["aid"]
    return [
        (
            'Write a short folk-tale-style story for a 3-to-5-year-old set on a loose gravel path, '
            'and include the word "excellent".'
        ),
        (
            f"Tell a brave story where a little {hero.type} hears trouble on a loose gravel path, "
            f"uses {aid.phrase}, and earns a surprise happy ending."
        ),
        (
            f"Write a gentle rescue tale about {problem.creature_phrase} in danger, where careful courage matters more than strength."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    aid = f["aid"]
    surprise = f["surprise"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {f['hero_name']}, a little {hero.type} walking along a loose gravel path. "
            f"The child stopped because {problem.creature_phrase} was in trouble."
        ),
        (
            "What was the trouble on the path?",
            f"{problem.creature_phrase.capitalize()} {problem.peril}. "
            f"The loose stones made the rescue harder because they could slip underfoot."
        ),
        (
            f"Why was {f['hero_name']} brave?",
            f"{f['hero_name']} stayed to help instead of running away from the risky place. "
            f"The child moved carefully on the loose gravel path and chose a way to rescue that truly fit the danger."
        ),
        (
            f"How did {f['hero_name']} solve the problem?",
            f"{f['hero_name']} {aid.qa_text}. "
            f"That worked because {aid.label} matched what the rescue needed on the slipping path."
        ),
        (
            "What was the surprise at the end?",
            f"The surprise was that {surprise.giver} appeared after the rescue and gave the child {surprise.gift}. "
            f"It turned the brave act into a happy ending with an unexpected reward."
        ),
        (
            "How did the story end?",
            f"It ended happily, with the trouble safe and the child walking home gladder than before. "
            f"The final image shows that kindness on a hard road brought back goodness in return."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"gravel", "bravery", "surprise"}
    problem = world.facts["problem"]
    aid = world.facts["aid"]
    if problem.id == "lamb_gully":
        tags.add("lamb")
    elif problem.id == "sparrow_thorn":
        tags.add("sparrow")
    elif problem.id == "cart_wheel":
        tags.add("cart")
    if aid.id == "rope":
        tags.add("rope")
    if aid.id == "walking_stick":
        tags.add("stick")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
needs_stable(P) :- problem(P), req_stable(P).
needs_reach(P)  :- problem(P), req_reach(P).
needs_pull(P)   :- problem(P), req_pull(P).

fits(P, A) :- problem(P), aid(A),
              not needs_stable(P).
fits(P, A) :- problem(P), aid(A),
              needs_stable(P), stable(A),
              not needs_reach(P), not needs_pull(P).
fits(P, A) :- problem(P), aid(A),
              needs_stable(P), stable(A),
              needs_reach(P), reach(A),
              not needs_pull(P).
fits(P, A) :- problem(P), aid(A),
              needs_stable(P), stable(A),
              not needs_reach(P),
              needs_pull(P), pull(A).
fits(P, A) :- problem(P), aid(A),
              needs_stable(P), stable(A),
              needs_reach(P), reach(A),
              needs_pull(P), pull(A).
fits(P, A) :- problem(P), aid(A),
              not needs_stable(P),
              needs_reach(P), reach(A),
              not needs_pull(P).
fits(P, A) :- problem(P), aid(A),
              not needs_stable(P),
              not needs_reach(P),
              needs_pull(P), pull(A).
fits(P, A) :- problem(P), aid(A),
              not needs_stable(P),
              needs_reach(P), reach(A),
              needs_pull(P), pull(A).

valid(P, A, S) :- problem(P), aid(A), surprise(S), fits(P, A).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if problem.need_stable:
            lines.append(asp.fact("req_stable", pid))
        if problem.need_reach:
            lines.append(asp.fact("req_reach", pid))
        if problem.need_pull:
            lines.append(asp.fact("req_pull", pid))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        if aid.stable:
            lines.append(asp.fact("stable", aid_id))
        if aid.reach:
            lines.append(asp.fact("reach", aid_id))
        if aid.pull:
            lines.append(asp.fact("pull", aid_id))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def _check_params(params: StoryParams) -> None:
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem '{params.problem}'.)")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid '{params.aid}'.)")
    if params.surprise not in SURPRISES:
        raise StoryError(f"(Unknown surprise '{params.surprise}'.)")
    if not aid_fits(PROBLEMS[params.problem], AIDS[params.aid]):
        raise StoryError(explain_rejection(PROBLEMS[params.problem], AIDS[params.aid]))
    if params.gender not in {"girl", "boy"}:
        raise StoryError("(Gender must be 'girl' or 'boy'.)")


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "excellent" not in sample.story.lower():
            raise StoryError("(Smoke test failed: generated story missing expected content.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale storyworld about bravery on a loose gravel path. "
        "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--aid", choices=sorted(AIDS))
    ap.add_argument("--surprise", choices=sorted(SURPRISES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.aid:
        problem = PROBLEMS[args.problem]
        aid = AIDS[args.aid]
        if not aid_fits(problem, aid):
            raise StoryError(explain_rejection(problem, aid))

    combos = [
        combo for combo in valid_combos()
        if (args.problem is None or combo[0] == args.problem)
        and (args.aid is None or combo[1] == args.aid)
        and (args.surprise is None or combo[2] == args.surprise)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    problem_id, aid_id, surprise_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    trait = rng.choice(TRAITS)
    return StoryParams(
        problem=problem_id,
        aid=aid_id,
        surprise=surprise_id,
        name=name,
        gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    _check_params(params)
    world = tell(
        problem=PROBLEMS[params.problem],
        aid=AIDS[params.aid],
        surprise=SURPRISES[params.surprise],
        name=params.name,
        gender=params.gender,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (problem, aid, surprise) combos:\n")
        for problem, aid, surprise in combos:
            print(f"  {problem:14} {aid:14} {surprise}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.problem} with {p.aid} ({p.surprise})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
