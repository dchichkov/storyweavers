#!/usr/bin/env python3
"""
Generated storyworld: glitchy basement stairs resolved by kindness in a comedic tone.
Based on seed word "glitch", set on basement stairs, featuring kindness in Comedy style.
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

# ===== Domain Building Blocks =====
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "object"           # stair_step, kid, parent, tool, ...
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        subject_map = {"kid": "she", "mom": "she", "dad": "he", "stair_step": "it"}
        object_map = {"kid": "her", "mom": "her", "dad": "him", "stair_step": "it"}
        possessive_map = {"kid": "her", "mom": "her", "dad": "his", "stair_step": "its"}
        lookup = {"subject": subject_map, "object": object_map, "possessive": possessive_map}
        return lookup[case].get(self.type, "it")

    @property
    def it(self) -> str:
        return "them" if self.plural else "it"

@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

# ===== Cause Rules =====
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_step_glitches(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["waiting"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.id != "basement_stairs" or 'loose' not in item.meters:
                continue
            if ("step", actor.id, "loose") in world.fired:
                continue
            world.fired.add(("step", actor.id, "loose"))
            item.meters["loose"] += 0.8
            item.meters["noisy"] += max(0, 0.5 - item.meters["loose"])
            actor.memes["frustration"] += 0.9
            return [
                f"{actor.phrase} stepped onto the basement stairs, and they felt even wobblier than before."
            ]
    return []

def _r_frustration_energy(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["frustration"] > THRESHOLD:
            if ("frustrate_act", actor.id) in world.fired:
                continue
            world.fired.add(("frustrate_act", actor.id))
            actor.memes["futile_work"] += 1.0
            return [
                f"{actor.phrase} huffed and puffed and tried to kick the wobbly step back into place..."
            ]
    return []

def _r_futile_work_spreads_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["futile_work"] > THRESHOLD:
            stairs = world.get("basement_stairs")
            if ("mess_up", stairs.id) in world.fired:
                continue
            world.fired.add(("mess_up", stairs.id))
            stairs.meters["cracked"] += 1.2
            stairs.meters["loose"] += 0.3
            return [
                "A tiny crack ran down the riser, and the step now wobbled like jelly."
            ]
    return []

def _r_kindness_cools_tension(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["joy"] > 0.5 and ("resolved", "teamwork") in world.fired:
            return [
                f"{actor.phrase} grinned. Things didn’t feel like a glitch anymore; they felt like an adventure shared with {world.get('parent').phrase}."
            ]
    return []

CAUSAL_RULES: list[Rule] = [
    Rule(name="step_glitches", tag="physical", apply=_r_step_glitches),
    Rule(name="frustration_energy", tag="emotional", apply=_r_frustration_energy),
    Rule(name="futile_work_spreads_mess", tag="physical", apply=_r_futile_work_spreads_mess),
    Rule(name="kindness_cools_tension", tag="emotional", apply=_r_kindness_cools_tension),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

# ===== Registries =====
@dataclass
class BasementSetting:
    id: str
    phrase: str

@dataclass
class Glitch:
    id: str
    actor_phrase: str
    verb: str
    gerund: str
    mess_key: str
    symptom: str
    tags: set[str]

@dataclass
class KindnessAct:
    id: str
    phrase: str
    label: str
    effect_tag: str

BASEMENTS = {
    "cellar": BasementSetting(id="cellar", phrase="the creaky cellar stairs"),
    "basement": BasementSetting(id="basement", phrase="the shadowy basement steps"),
}

GLITCHES = {
    "loose": Glitch(
        id="loose",
        actor_phrase="a wobbly step",
        verb="notice a step is wobbly",
        gerund="noticing the step felt wobbly",
        mess_key="loose",
        symptom="the riser tilted underfoot",
        tags={"loose", "wobble"},
    ),
    "squeaky": Glitch(
        id="squeaky",
        actor_phrase="loud squeaking noises",
        verb="hear loud squeaks",
        gerund="hearing loud squeaks",
        mess_key="noisy",
        symptom="metallic shriek echoing off the walls",
        tags={"noise", "squeak"},
    ),
}

KINDNESS_ACTS = [
    KindnessAct(
        id="teamwork",
        phrase="worked together side-by-side",
        label="teamed up to fix it",
        effect_tag="teamwork",
    ),
    KindnessAct(
        id="joke",
        phrase="told a silly joke that made everyone giggle",
        label="shared a silly joke",
        effect_tag="laughter",
    ),
    KindnessAct(
        id="gentle_fix",
        phrase="tightened the screw with gentle turns till it held",
        label="secured the step gently",
        effect_tag="fixed",
    ),
]

GIRL_NAMES = ["Maya", "Lily", "Zoe", "Emma"]
BOY_NAMES = ["Leo", "Max", "Ben", "Sam"]
TRAITS = ["curious", "playful", "inventive", "carefree"]

# ===== Screenplay Beats =====
def introduce_kid(world: World, name: str, gender: str, traits: list[str]) -> None:
    trait_str = traits[0] if traits else "little"
    phrase = f"{trait_str} {gender} named {name}"
    kid = world.add(Entity(id="kid", kind="character", type=gender, label=phrase,
                          phrase=f"{name}", traits=traits))
    kid.memes["playful"] = 0.8
    world.say(f"{name} was a {trait_str} {gender} who loved exploring the passageways below.")

def buy_or_find_kid_basement(who: Entity, phrase: str) -> None:
    pass  # parent action handled at call site

def discover_glitch(world: World, glitch: Glitch, kid: Entity) -> None:
    kid.memes["waiting"] += 0.95
    world.say(f"One afternoon, {kid.phrase} climbed down {world.place} and {glitch.verb}.")

def identify_glitch_detail(glitch: Glitch, kid: Entity) -> str:
    noun = "step" if glitch.id == "loose" else "stairs"
    return f"{kid.phrase} frowned: the {noun} kept {glitch.mess_key} and {glitch.symptom}."

def warn_doorstep(world: World, parent: Entity, kid: Entity) -> None:
    world.say(
        f'"Hang on, {kid.phrase}!" {parent.phrase} called from behind. '
        f'"That section sure has been {glitch.verb.split()[-1]} lately."'
    )

def try_improvised_fix(world: World, kid: Entity, glitch: Glitch) -> None:
    kid.memes["futile_work"] += 1.2
    world.say(
        f"{kid.phrase} grabbed a nearby tool—a toy hammer—and gave the wobble a good whack. "
        f"The noise made the basement walls hum."
    )
    stairs = world.get("basement_stairs")
    stairs.meters["cracked"] += 0.7
    stairs.meters["loose"] += 0.5
    propagate(world)

def tell_silly_joke(parent: Entity, kid: Entity) -> str:
    jokes = [
        '"Why did the step climb upstairs?", ' '"To see what all the fuss was about!"',
        '"Knock knock.", "Who’s there?", ' '"Glitch. Glitch who?", "Glitch your basement lights!"',
    ]
    return f'{parent.phrase} cupped {parent.pronoun("object")} hands and volunteered: {jokes[0]}{jokes[1]}'

def work_together(parent: Entity, kid: Entity, act: KindnessAct, stairs: Entity) -> None:
    kid.memes["joy"] += 1.1
    parent.memes["joy"] += 0.9
    stairs.meters["loose"] = max(0, stairs.meters["loose"] - 1.8)
    stairs.meters["cracked"] = max(0, stairs.meters["cracked"] - 0.4)
    world.fired.add(("resolved", act.effect_tag))
    world.say(
        f"{parent.phrase} showed {kid.phrase} how to hold the flashlight steady while {act.phrase} in unison. "
        f"Together they listened—the squeaks were gone, and the step felt solid once more."
    )

def conclude_story(world: World, act: KindnessAct) -> None:
    world.para()
    world.say(
        f"From that afternoon on, {world.get('kid').phrase} realized that a little {act.label} "
        f"was better than a lot of frantic hammering—and the basement had never felt friendlier."
    )

# ===== Core Generation =====
def build_story(basement_id: str, glitch_id: str, kindness_id: str,
                kid_name: str, kid_traits: list[str]) -> World:
    base = BASEMENTS[basement_id]
    glitch_def = GLITCHES[glitch_id]
    kindness_def = next(k for k in KINDNESS_ACTS if k.id == kindness_id)
    world = World(base.phrase)

    kid = introduce_kid(world, kid_name, kid_traits[0] if kid_traits else "kid", kid_traits)
    parent_type = "mom" if random.random() > 0.5 else "dad"
    parent = world.add(Entity(
        id="parent", kind="character", type=parent_type,
        phrase={ "mom": "Mom", "dad": "Dad" }[parent_type],
    ))

    stairs = world.add(Entity(
        id="basement_stairs", type="stair_step", label=glitch_def.actor_phrase,
        meters={"loose": 0.7, "noisy": 0.3, "cracked": 0.1}
    ))

    # Act 1
    world.paragraphs[-1].append(
        f"{kid.phrase} clomped down {world.place} on the way to {parent.phrase.capitalize()}'s workshop."
    )
    world.para()

    # Act 2
    discover_glitch(world, glitch_def, kid)
    world.say(identify_glitch_detail(glitch_def, kid))
    warn_doorstep(world, parent, kid)
    world.say(
        f"{kid.phrase} didn’t listen, though. {kid.pronoun('subject').capitalize()} "
        f"set {parent.pronoun('possessive')} toolbox lid aside and {glitch_def.verb}."
    )
    try_improvised_fix(world, kid, glitch_def)

    # Act 3
    world.para()
    world.say(tell_silly_joke(parent, kid))
    world.say(f"After a few giggles, {kid.phrase} exhaled. Maybe fixing wasn’t fun today.")
    work_together(parent, kid, kindness_def, stairs)
    conclude_story(world, kindness_def)

    # Facts for Q&A
    world.facts.update(
        kid=kid, parent=parent, stairs=stairs,
        basement=base, glitch=glitch_def, kindness=kindness_def,
        resolved=True, teamwork=(kindness_id == "teamwork"),
    )
    return world

# ===== Q&A Generators =====
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedy for ages 4–6 where a kid notices a "glitch" on the basement stairs, '
        f'tries a hasty fix, but a kind grown-up turns the mishap into a bonding moment.',
        f'Tell a gentle giggle-story where {f["kid"].phrase} meets an obstacle on the stairs '
        f'and learns that teamwork (or laughter) can make things right again.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid, parent = f["kid"], f["parent"]
    sub, obj, pos = kid.pronoun("subject"), kid.pronoun("object"), kid.pronoun("possessive")
    return [
        QAItem(
            question=f"Who lived in the house with {pos} {parent.phrase.lower()}?",
            answer=f"It was {kid.phrase} and {parent.phrase}.",
        ),
        QAItem(
            question=f"What made {kid.phrase} decide to try fixing whatever looked wrong on the stairs?",
            answer=(
                f"{kid.phrase} thought the wobbly step or loud squeaking looked easy to \"fix in a hurry,\" "
                f"but the moment {sub} started batting at it with a tool, the step felt even worse."
            ),
        ),
        QAItem(
            question="How did the parent help without scolding?",
            answer=(
                f"{parent.phrase} came downstairs and told a silly joke that made {obj} giggle, "
                f"then showed {obj} how to hold a flashlight together so they could see the real fix."
            ),
        ),
        QAItem(
            question="By the end of the story, were the dark stairs still scary?",
            answer=f"No! Once the teamwork fix took hold, the basement stairs even felt friendly.",
        ),
    ]

KNOWLEDGE = {
    "basement": [("What is a basement?",
                  "A basement is a room below the ground floor of a house; people often store things there.")],
    "glitch": [("What does 'glitch' mean?",
                "A glitch is a small, sudden fault or malfunction, like when something acts funny for a short time.")],
    "teamwork": [("Why is teamwork helpful?",
                  "Teamwork lets people share ideas, reduces mistakes, and makes hard tasks easier and happier.")],
}
KNOWLEDGE_ORDER = ["basement", "glitch", "teamwork"]

def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set()
    if f.get("glitch"):
        tags.update(f["glitch"].tags)
    if f.get("kindness"):
        tags.add(f["kindness"].id)
    tags.add("basement")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
    return out

# ===== ASP Twin =====
ASP_RULES = r"""
% A story is valid if it spotlights a basement staircase glitch resolved by kindness.
valid_story(Basement, Glitch, Kindness) :-
    basement(Basement), glitch(Glitch), kindness(Kindness).

% Ensure the selected glitch actually affects the basement type.
affects(loose, cellar).
affects(loose, basement).
affects(squeaky, cellar).
affects(squeaky, basement).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for bid, b in BASEMENTS.items():
        lines.append(asp.fact("basement", bid))
    for gid, g in GLITCHES.items():
        lines.append(asp.fact("glitch", gid))
        for t in g.tags:
            lines.append(asp.fact("tag", gid, t))
    for kid, k in enumerate(KINDNESS_ACTS):
        lines.append(asp.fact("kindness", k.id))
        lines.append(f":- kind_id({k.id}, {kid}).")  # unique index pseudo-fact
    return "\n".join(lines)

def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show or '#show valid_story/3.'}\n"

def asp_verify() -> int:
    try:
        import asp
        clingo_set = set(asp.atoms(asp.one_model(asp_program("#show valid_story/3.")), "valid_story"))
        python_pairs = [(b.id, g.id, k.id) for b in BASEMENTS.values()
                        for g in GLITCHES.values() for k in KINDNESS_ACTS]
        python_set = set((b, g, k) for (b, g, k) in python_pairs)
        if clingo_set == python_set:
            print(f"OK: clingo gate matches registries ({len(clingo_set)} combos).")
            return 0
        print("MISMATCH clingo vs Python registries:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        return 1
    except Exception as e:
        print("ASP verify error:", e)
        return 1

# ===== Parameters =====
@dataclass
class StoryParams:
    basement: str
    glitch: str
    kindness: str
    kid_name: str
    kid_traits: list[str]

CURATED = [
    StoryParams("cellar", "loose", "teamwork", "Maya", ["playful", "inventive"]),
    StoryParams("basement", "squeaky", "joke", "Leo", ["curious", "carefree"]),
]

# ===== CLI =====
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Basement-stairs glitch resolved with kindness in Comedy tone.")
    ap.add_argument("--basement", choices=BASEMENTS)
    ap.add_argument("--glitch", choices=GLITCHES)
    ap.add_argument("--kindness", choices=[k.id for k in KINDNESS_ACTS])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.glitch and args.kindness:
        # All combinations are considered valid in this tiny domain
        pass

    candidates = list(range(len(CURATED)))
    if args.basement or args.glitch or args.kindness:
        candidates = [i for i, p in enumerate(CURATED)
                      if (args.basement is None or p.basement == args.basement)
                      and (args.glitch is None or p.glitch == args.glitch)
                      and (args.kindness is None or p.kindness == args.kindness)]

    if not candidates:
        raise StoryError("(No curated variant matches the given filters.)")

    chosen = rng.choice(candidates)
    base = CURATED[chosen]
    name = args.name or base.kid_name
    traits = base.kid_traits.copy()
    if args.trait and args.trait not in traits:
        traits.append(args.trait)
    if not traits and args.gender:
        traits.append({ "girl": "playful", "boy": "curious" }[args.gender])
    random.shuffle(traits)
    return StoryParams(
        basement=args.basement or base.basement,
        glitch=args.glitch or base.glitch,
        kindness=args.kindness or base.kindness,
        kid_name=name,
        kid_traits=traits[:2] or base.kid_traits,
    )

def generate(params: StoryParams) -> StorySample:
    world = build_story(
        params.basement, params.glitch, params.kindness,
        params.kid_name, params.kid_traits,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        from collections import Counter
        lines = ["--- world model state ---"]
        for e in sample.world.entities.values():
            m = {k: v for k, v in e.meters.items() if v >= THRESHOLD}
            me = {k: v for k, v in e.memes.items() if v >= THRESHOLD}
            bits = []
            if m:
                bits.append(f"meters={m}")
            if me:
                bits.append(f"memes={me}")
            lines.append(f"  {e.id:12} {bits or '(quiet)'}")
        if sample.world.facts:
            lines.append("facts: " + ", ".join(sample.world.facts.keys()))
        print("\n".join(lines))
    if qa:
        print()
        lines = []
        for idx, block in enumerate([("Prompts:", sample.prompts),
                                     ("Story Q&A:", [(q.question, q.answer) for q in sample.story_qa]),
                                     ("World Q&A:", [(q.question, q.answer) for q in sample.world_qa])]):
            lines.append(f"== ({idx+1}) {block[0]} ==")
            if block[1]:
                for item in block[1]:
                    if isinstance(item, tuple):
                        q, a = item
                        lines.append(f"Q: {q}\nA: {a}")
                    else:
                        lines.append(f"- {item}")
        print("\n".join(lines))

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("/* episode: glitch basement comedy */"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
            models = asp.solve(asp_program("#show valid_story/3."), models=0)
            print(f"{len(models)} combinatorial variants via ASP:")
            for m in models:
                atoms = asp.atoms(m, "valid_story")
                if atoms:
                    print(" -", " / ".join(str(a) for a in atoms[0]))
        except Exception as e:
            print("CLINGO not available for ASP listing:", e)
        return

    rng = random.Random(args.seed)
    if args.all:
        samples = [generate(CURATED[i]) for i in range(len(CURATED))]
    else:
        rng = random.Random(args.seed if args.seed is not None else rng.randrange(2**31))
        samples = []
        seen = set()
        tries = 0
        while len(samples) < args.n and tries < args.n * 20:
            tries += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            sample = generate(params)
            key = (sample.params.kid_name, sample.params.basement,
                   sample.params.glitch, sample.params.kindness)
            if key in seen:
                continue
            seen.add(key)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, s in enumerate(samples):
        header = f"### {s.params.kid_name}: {s.params.glitch} glitch on {s.params.basement} stairs"
        if len(samples) > 1:
            header += f" (variant {idx+1})"
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
