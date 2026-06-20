#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.3-codex-spark/confuse_brickle_repetition_dialogue_bedtime_story.py
===============================================================================

Bedtime-story world for a seed with the words: confuse, brickle.
Features required: Repetition, Dialogue.

Source tale
-----------
At the evening lamp-lighting, a child and a gentle helper hear a soft repeated
brickle sound around bedtime preparations. The sound repeats so much that it
confuses the child at first, so they pause, listen, and trace the noise to a
physical object. After choosing the right method, the repetition resolves and the
closing image proves the room is finally safe and sleepy.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve()
for candidate in Path(__file__).resolve().parents:
    if (candidate / "storyworlds" / "results.py").exists():
        ROOT = candidate
        break
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402

BEDTIME_HOME = "Maple Lantern Home"


@dataclass(frozen=True)
class Scene:
    key: str
    phrase: str
    opening_image: str
    ending_image: str
    allowed_methods: tuple[str, ...]


@dataclass(frozen=True)
class Problem:
    key: str
    label: str
    scene: str
    signal_text: str
    refrain: str
    observation: str
    cause: str
    need: str
    after_refrain: str
    settled_image: str
    compatible_methods: tuple[str, ...]


@dataclass(frozen=True)
class Method:
    key: str
    phrase: str
    action_text: str
    why_it_fits: str
    solves: str
    opening_line: str


@dataclass
class StoryParams:
    scene: str
    problem: str
    method: str
    hero: str
    hero_kind: str
    helper: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    phrase: str
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"girl", "mother", "grandmother", "aunt", "woman", "nurse"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind in {"boy", "father", "grandfather", "uncle", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Beat:
    key: str
    text: str


@dataclass
class World:
    params: StoryParams
    scene_cfg: Scene
    problem_cfg: Problem
    method_cfg: Method
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    history: list[Beat] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.name] = ent
        return ent

    def get(self, name: str) -> Entity:
        return self.entities[name]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def note(self, key: str, text: str) -> None:
        self.history.append(Beat(key=key, text=text))

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(f"  scene={self.scene_cfg.key}")
        rows.append(f"  problem={self.problem_cfg.key}")
        rows.append(f"  method={self.method_cfg.key}")
        for ent in self.entities.values():
            rows.append(
                f"  {ent.name}<{ent.kind}> location={ent.location} "
                f"meters={dict(ent.meters)} memes={dict(ent.memes)}"
            )
        rows.append(f"  facts={self.facts}")
        rows.append("  history:")
        for beat in self.history:
            rows.append(f"    - {beat.key}: {beat.text}")
        return "\n".join(rows)


SCENES: dict[str, Scene] = {
    "window_nook": Scene(
        key="window_nook",
        phrase="the window nook beside a moon curtain",
        opening_image=(
            "a yellow night lamp glowed near the blanket basket, and the windows had tiny stars taped in place"
        ),
        ending_image=(
            "the moon curtain settled without shaking, and the whole room looked soft and sleepy"
        ),
        allowed_methods=("tighten_latch", "straighten_tie"),
    ),
    "story_cabin": Scene(
        key="story_cabin",
        phrase="the story cabin built from old cushions and a low shelf",
        opening_image=(
            "a small night-shelf looked like a fort, with a brass bell-shaped lamp already trimmed for bedtime"
        ),
        ending_image=(
            "the story shelf stood still, and even the pillows seemed to flatten into calm"
        ),
        allowed_methods=("tighten_latch", "mend_soft_ribbon"),
    ),
}

PROBLEMS: dict[str, Problem] = {
    "loose_bell_latch": Problem(
        key="loose_bell_latch",
        label="the small brass bell by the window",
        scene="window_nook",
        signal_text="a tiny brickle, brickle, brickle from the bell stand",
        refrain='"brickle, brickle, brickle, brickle."',
        observation="The cloth near the stand touched the stand in a little loop, then slid away.",
        cause="the tiny latch holding the wind thread had slipped out of its notch.",
        need="anchor",
        after_refrain='"brickle, brickle, brickle," soft as a single sigh.',
        settled_image=(
            "the bell thread stayed straight, and the brass stand no longer tapped in little jerks"
        ),
        compatible_methods=("tighten_latch",),
    ),
    "shelf_jingle_knot": Problem(
        key="shelf_jingle_knot",
        label="a shell charm near the story shelf",
        scene="story_cabin",
        signal_text="a brickle, brickle, brickle rhythm from a shell charm string",
        refrain='"brickle, brickle, brickle, brickle."',
        observation="One ribbon had twisted and was brushing the shell each time the room sighed with air.",
        cause="the helper ribbon had wrapped once too many times and pulled the charm askew.",
        need="untie",
        after_refrain='"brickle" came once, then faded to a friendly hush.',
        settled_image=(
            "the shell charm tilted into its nest and stopped tapping against the shelf"
        ),
        compatible_methods=("mend_soft_ribbon",),
    ),
}

METHODS: dict[str, Method] = {
    "tighten_latch": Method(
        key="tighten_latch",
        phrase="tighten the loose bell latch with two careful turns",
        action_text=(
            "{hero} steadied the thread and {helper} held the brass stand. "
            "Together they tightened the tiny latch one turn, then one more, so the thread could breathe without slipping."
        ),
        why_it_fits="A loose latch is exactly what creates an anchored loop that knocks in a brickle pattern.",
        solves="anchor",
        opening_line='"Don\'t worry. Let\'s just hold it steady and tighten that latch," said {hero}.',
    ),
    "straighten_tie": Method(
        key="straighten_tie",
        phrase="straighten the hanging tie where it has wrapped too tightly",
        action_text=(
            "{hero} unwound the thin tie while {helper} counted soft breathes with them. "
            "The tie was set back so it guided the thread instead of snapping it." 
        ),
        why_it_fits=(
            "Some night noises come from a thread that is bent around itself, so this method calms that path."
        ),
        solves="anchor",
        opening_line='"Could this be a crooked tie?" {helper} asked, pointing at the thread.',
    ),
    "mend_soft_ribbon": Method(
        key="mend_soft_ribbon",
        phrase="untie the knot and wrap the ribbon with a soft knot",
        action_text=(
            "{hero} and {helper} lifted the shelf shell, untied the tight knot, "
            "and tied it into a soft loop so the charm could sit steady."
        ),
        why_it_fits="A ribbon knot that drags through a shelf path creates the repeated brickle taps we keep hearing.",
        solves="untie",
        opening_line='"Let me touch the string," said {helper}, "a soft ribbon knot can make enough change."',
    ),
}

HERO_NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Luna", "Mina", "Nell", "Poppy"),
    "boy": ("Theo", "Ben", "Noah", "Ravi"),
}

HELPERS = (
    "Grandma Rowan",
    "Mama Elara",
    "Uncle Juniper",
    "Aunt Sable",
)



def _pick_hero(hero_kind: str, rng: random.Random) -> str:
    return rng.choice(HERO_NAMES[hero_kind])



def _pick_helper(rng: random.Random) -> str:
    return rng.choice(HELPERS)



def valid_combo(scene_key: str, problem_key: str, method_key: str) -> bool:
    if scene_key not in SCENES or problem_key not in PROBLEMS or method_key not in METHODS:
        return False

    scene = SCENES[scene_key]
    problem = PROBLEMS[problem_key]
    method = METHODS[method_key]

    return (
        problem.scene == scene.key
        and method.key in scene.allowed_methods
        and method.key in problem.compatible_methods
        and method.solves == problem.need
    )



def invalid_reason(scene_key: str, problem_key: str, method_key: str) -> str:
    if scene_key not in SCENES:
        return f"No story: unknown scene {scene_key!r}."
    if problem_key not in PROBLEMS:
        return f"No story: unknown problem {problem_key!r}."
    if method_key not in METHODS:
        return f"No story: unknown method {method_key!r}."

    scene = SCENES[scene_key]
    problem = PROBLEMS[problem_key]
    method = METHODS[method_key]

    if problem.scene != scene.key:
        return (
            f"No story: {problem.label} does not belong in {scene.phrase}. "
            f"It belongs in {SCENES[problem.scene].phrase}."
        )
    if method.key not in scene.allowed_methods:
        return (
            f"No story: {scene.phrase} cannot host method {method.phrase}. "
            f"Try one of: {', '.join(scene.allowed_methods)}."
        )
        if method.key not in problem.compatible_methods:
            return (
                f"No story: method {method.phrase} does not match this problem. "
                f"This problem needs a solution of type {problem.need}."
            )
    if method.solves != problem.need:
        return (
            f"No story: method {method.phrase} solves {method.solves}, "
            f"but this problem needs {problem.need}."
        )
    return "No story: invalid combination."



def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for scene_key in sorted(SCENES):
        for problem_key in sorted(PROBLEMS):
            for method_key in sorted(METHODS):
                if valid_combo(scene_key, problem_key, method_key):
                    combos.append((scene_key, problem_key, method_key))
    return combos



def _matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    combos = valid_combos()
    filtered = [
        combo
        for combo in combos
        if (args.scene is None or combo[0] == args.scene)
        and (args.problem is None or combo[1] == args.problem)
        and (args.method is None or combo[2] == args.method)
    ]

    if args.scene and args.problem and args.method and not filtered:
        raise StoryError(invalid_reason(args.scene, args.problem, args.method))

    if not filtered:
        if args.scene or args.problem or args.method:
            raise StoryError("No story: no valid scene/problem/method combination matches the requested filters.")
        return combos

    return filtered



def _params_from_combo(
    args: argparse.Namespace,
    combo: tuple[str, str, str],
    index: int = 0,
) -> StoryParams:
    rng = random.Random(args.seed + index)
    scene_key, problem_key, method_key = combo
    hero_kind = args.hero_kind or rng.choice(sorted(HERO_NAMES))
    return StoryParams(
        scene=scene_key,
        problem=problem_key,
        method=method_key,
        hero=args.hero or _pick_hero(hero_kind, rng),
        hero_kind=hero_kind,
        helper=args.helper or _pick_helper(rng),
        seed=args.seed + index,
    )



def reasonableness_gate(params: StoryParams) -> None:
    if not valid_combo(params.scene, params.problem, params.method):
        raise StoryError(invalid_reason(params.scene, params.problem, params.method))



def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    scene_cfg = SCENES[params.scene]
    problem_cfg = PROBLEMS[params.problem]
    method_cfg = METHODS[params.method]

    world = World(params=params, scene_cfg=scene_cfg, problem_cfg=problem_cfg, method_cfg=method_cfg)

    hero = world.add(
        Entity(
            name=params.hero,
            kind=params.hero_kind,
            phrase=f"little {params.hero_kind}",
            location=scene_cfg.key,
            meters={"attention": 1.0, "steps": 0.0},
            memes={"curiosity": 1.0, "confusion": 0.1, "relief": 0.0},
        )
    )
    helper = world.add(
        Entity(
            name=params.helper,
            kind="helper",
            phrase="soft-spoken helper",
            location=scene_cfg.key,
            meters={"steadying": 1.0},
            memes={"calm": 1.1, "care": 1.0},
        )
    )
    world.add(
        Entity(
            name=scene_cfg.key,
            kind="scene",
            phrase=scene_cfg.phrase,
            location=scene_cfg.key,
            meters={"peace": 1.0, "prepared": 1.0},
            memes={"safety": 1.0},
        )
    )
    world.add(
        Entity(
            name=problem_cfg.key,
            kind="noise",
            phrase=problem_cfg.label,
            location=scene_cfg.key,
            meters={"signal": 0.0, "resolved": 0.0, "risk": 0.8},
            memes={"need": 1.0},
        )
    )
    world.add(
        Entity(
            name=method_cfg.key,
            kind="method",
            phrase=method_cfg.phrase,
            location=scene_cfg.key,
            meters={"ready": 1.0},
            memes={"helpful": 1.0},
        )
    )

    hero.meters["steps"] += 1.0
    world.facts.update(
        {
            "setting": BEDTIME_HOME,
            "style": "bedtime",
            "feature": "repetition,dialogue",
            "seed_word_1": "confuse",
            "seed_word_2": "brickle",
            "hero": hero.name,
            "helper": helper.name,
            "scene": scene_cfg.key,
            "problem": problem_cfg.key,
            "method": method_cfg.key,
            "seed": str(params.seed),
        }
    )
    world.note("created", f"scene={scene_cfg.key} problem={problem_cfg.key} method={method_cfg.key}")
    return world



def _hero(world: World) -> Entity:
    return world.get(world.params.hero)



def _helper(world: World) -> Entity:
    return world.get(world.params.helper)



def _problem(world: World) -> Entity:
    return world.get(world.params.problem)



def _introduce(world: World) -> None:
    hero = _hero(world)
    scene = world.scene_cfg
    world.say(
        f"At {BEDTIME_HOME}, {hero.name} and {world.params.helper} finished up at {scene.phrase}. "
        f"A soft lamp glow made the blankets and pillows look like little clouds, and {scene.opening_image}."
    )
    world.say(
        f"{hero.name} was learning bedtime routines, so {hero.pronoun('subject')} kept everything neat before sleep."
    )
    world.note("introduced", f"hero={hero.name} at {scene.key}")



def _hear_repetition(world: World) -> None:
    hero = _hero(world)
    helper = _helper(world)
    problem = world.problem_cfg
    problem_ent = _problem(world)
    world.para()

    hero.memes["confusion"] += 0.7
    helper.memes["care"] += 0.2
    problem_ent.meters["signal"] = 1.2
    problem_ent.meters["risk"] = 1.2
    world.note("heard", f"signal_started:{problem.key}")

    world.say(
        f"Then came a sound from near {problem.label}: {problem.signal_text}. "
        f'The line arrived three times: {problem.refrain}, and once more {problem.refrain}'
    )
    world.say(
        f'"This brickle makes me confuse," {hero.name} confessed softly. "I think I heard it before, but I cannot place it."'
    )
    world.say(
        f'"Let\'s not guess," {helper.name} whispered. "We will find the source first, then fix it slowly."'
    )
    world.say(
        f"The repeated sound was still there because the cause had not changed yet: {problem.observation}"
    )



def _investigate_and_act(world: World) -> None:
    hero = _hero(world)
    helper = _helper(world)
    method = world.method_cfg
    problem = world.problem_cfg
    scene = world.scene_cfg
    problem_ent = _problem(world)

    world.para()
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 0.6
    problem_ent.memes["need"] = 1.0
    world.note("investigated", f"method={method.key}")

    world.say(method.opening_line.format(hero=hero.name, helper=helper.name))
    world.say(f"In {scene.phrase}, this was the best clue: {problem.cause}")
    world.say(method.action_text.format(hero=hero.name, helper=helper.name))
    world.say(f"It works because {method.why_it_fits}")
    hero.memes["confusion"] = max(0.0, hero.memes["confusion"] - 0.6)
    problem_ent.meters["signal"] = 0.2
    world.say(
        f'Soon the noise thinned. It came again, now just once: {problem.after_refrain}'
    )



def _resolve(world: World) -> None:
    hero = _hero(world)
    helper = _helper(world)
    scene = world.scene_cfg
    problem = world.problem_cfg
    method = world.method_cfg
    problem_ent = _problem(world)

    hero.memes["relief"] += 1.1
    hero.memes["confusion"] = max(0.0, hero.memes["confusion"] - 0.3)
    helper.memes["calm"] += 0.4
    problem_ent.meters["signal"] = 0.0
    problem_ent.meters["risk"] = 0.0
    problem_ent.meters["resolved"] = 1.0
    problem_ent.memes["need"] = 0.0
    world.note("resolved", f"problem={problem.key} method={method.key}")

    world.para()
    world.say(
        f'"Listen," said {helper.name}, and {hero.name} nodded as the room answered with quiet. {problem.after_refrain}'
    )
    world.say(
        f"The final image proved it: {problem.settled_image}, and then {scene.ending_image}."
    )
    world.say(
        f"By the time blankets were tucked, {hero.name} learned that repeated brickle sounds can be solved by checking what is physically loose rather than worrying about what the sound means."
    )



def simulate(world: World) -> World:
    _introduce(world)
    _hear_repetition(world)
    _investigate_and_act(world)
    _resolve(world)
    return world



def _prompts(world: World) -> list[str]:
    return [
        f"Write a child-friendly bedtime story set at {BEDTIME_HOME} around nighttime small-world sounds.",
        f"Include the word confuse and keep the repeated brickle noise as a meaningful clue in the plot.",
        f"Use dialogue and a clear state change, then end with a concrete visual that proves the room is safe for sleep at {world.scene_cfg.phrase}.",
    ]



def _story_qa(world: World) -> list[QAItem]:
    hero = world.params.hero
    helper = world.params.helper
    problem = world.problem_cfg
    method = world.method_cfg
    return [
        QAItem(
            "Why was the child confused at first?",
            f"The child became confused because the brickle sound kept repeating without an obvious source, and it seemed to drift between familiar and unknown sounds. "
            "Before anything was touched, the repeated phrase did not match a direct visible action, so the uncertainty stayed in the room.",
        ),
        QAItem(
            f"What was the repeated line in the story?",
            f"The repeat was {problem.refrain}, which was tied to the same physical sound source each time the scene stayed unchanged. "
            f"It repeated because the world state kept the problem active and the physical cause had not been fixed yet.",
        ),
        QAItem(
            f"How did {hero} and {helper} solve the problem?",
            f"They talked through the options first and then used {method.phrase}, which directly matched the cause in the scene. "
            f"After they applied that method, the signal weakened, the cause was corrected, and the meter for the problem moved from active to resolved.",
        ),
        QAItem(
            "How did the ending prove what changed in the world?",
            f"The ending image showed the previous sound object no longer tapping and the room settling into stillness. "
            f"That final image is evidence that the scene state changed: the conflict was not just described away, but physically fixed in the world.",
        ),
    ]



def _world_qa(world: World) -> list[QAItem]:
    problem = world.problem_cfg
    method = world.method_cfg
    return [
        QAItem(
            "Why is this story only generated for compatible scene/problem/method choices?",
            f"Each combination is checked by a compatibility rule: the chosen problem must belong to the scene, and the method must be allowed by both the scene and the problem\'s needed fix. "
            f"If that structure does not align, the reasonableness gate rejects the request before generation.",
        ),
        QAItem(
            "Where is the brickle problem carried in the world model?",
            f"The problem is carried by a physical issue entity in the same scene, not by abstract narration. "
            f"In this sample that entity is {problem.label}, and it stores a measurable signal meter plus a need marker.",
        ),
        QAItem(
            "What does the trace show about repetition and resolution?",
            f"The trace records repeated observation before the fix and a resolved state change after the action. "
            f"You can see the same world object go from a noisy signal to 0.0, and its risk meter drops while resolved becomes active.",
        ),
        QAItem(
            "Why does dialogue appear at the key moments instead of only narration?",
            f"Dialogue is used to explain uncertainty and plan before action, which fits the bedtime style with a child conversation. "
            f"It also grounds causality by tying the decision to a real-world method, then showing the consequence in state.",
        ),
    ]



def generate(params: StoryParams) -> StorySample:
    world = simulate(build_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


ASP_RULES = r"""
combo(S,P,M) :-
    scene(S),
    problem(P),
    method(M),
    issue_at(P,S),
    scene_allows(S,M),
    issue_allows(P,M),
    method_fixes(M,N),
    issue_needs(P,N).

ok :-
    chosen(S,P,M),
    combo(S,P,M).

#show combo/3.
#show ok/0.
"""



def asp_facts() -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for scene_key, scene in sorted(SCENES.items()):
        rows.append(fact("scene", scene_key))
        for method_key in scene.allowed_methods:
            rows.append(fact("scene_allows", scene_key, method_key))
    for problem_key, problem in sorted(PROBLEMS.items()):
        rows.append(fact("problem", problem_key))
        rows.append(fact("issue_at", problem_key, problem.scene))
        rows.append(fact("issue_needs", problem_key, problem.need))
        for method_key in problem.compatible_methods:
            rows.append(fact("issue_allows", problem_key, method_key))
    for method_key, method in sorted(METHODS.items()):
        rows.append(fact("method", method_key))
        rows.append(fact("method_fixes", method_key, method.solves))
    return "\n".join(rows) + "\n"



def asp_program(params: StoryParams | None = None) -> str:
    chosen = ""
    if params is not None:
        from storyworlds.asp import fact

        chosen = fact("chosen", params.scene, params.problem, params.method) + "\n"
    return asp_facts() + chosen + ASP_RULES



def asp_valid_combos() -> set[tuple[str, str, str]]:
    from storyworlds.asp import atoms, solve

    combos: set[tuple[str, str, str]] = set()
    for model in solve(asp_program(), models=0):
        combos.update(atoms(model, "combo"))
    return combos



def _asp_accepts(params: StoryParams) -> bool:
    from storyworlds.asp import atoms, one_model

    model = one_model(asp_program(params))
    return bool(atoms(model, "ok"))



def verify() -> str:
    python_set = set(valid_combos())
    asp_set = asp_valid_combos()
    if python_set != asp_set:
        only_python = sorted(python_set - asp_set)
        only_asp = sorted(asp_set - python_set)
        raise StoryError(
            f"ASP/Python mismatch. only_python={only_python} only_asp={only_asp}"
        )

    for index, combo in enumerate(sorted(python_set), 1):
        params = StoryParams(
            scene=combo[0],
            problem=combo[1],
            method=combo[2],
            hero=HERO_NAMES["girl"][0],
            hero_kind="girl",
            helper=HELPERS[0],
            seed=index,
        )
        if not _asp_accepts(params):
            raise StoryError(f"ASP failed to accept valid combo {combo!r}.")

        sample = generate(params)
        if sample.world is None:
            raise StoryError(f"Generated sample missing live world for {combo!r}.")
        lower_story = sample.story.lower()
        if "brickle" not in lower_story:
            raise StoryError(f"Generated story for {combo!r} forgot required word 'brickle'.")
        if "confuse" not in lower_story:
            raise StoryError(f"Generated story for {combo!r} forgot required word 'confuse'.")
        if lower_story.count("brickle") < 3:
            raise StoryError(f"Generated story for {combo!r} lost repetition-driven brickle presence.")
        if sample.story.count('"') < 2:
            raise StoryError(f"Generated story for {combo!r} has no dialogue quotes.")
        if "{" in sample.story or "}" in sample.story:
            raise StoryError(f"Generated story for {combo!r} leaked a template field.")
        if sample.story.count("\n\n") < 3:
            raise StoryError(f"Generated story for {combo!r} missed full beginning/turn/ending pacing.")
        if len(sample.prompts) != 3:
            raise StoryError(f"Generated story for {combo!r} has the wrong number of prompts.")
        if len(sample.story_qa) < 4 or len(sample.world_qa) < 4:
            raise StoryError(f"Generated story for {combo!r} has incomplete QA sets.")
        for qa in sample.story_qa:
            if qa.answer.count(".") < 2:
                raise StoryError(f"Story QA answer is too thin for {combo!r}: {qa.question!r}")
        for qa in sample.world_qa:
            if qa.answer.count(".") < 2:
                raise StoryError(f"World QA answer is too thin for {combo!r}: {qa.question!r}")

    return (
        f"OK: {len(python_set)} valid combos; ASP parity holds; generated stories pass"
        " quality checks for bedtime, repetition, and dialogue."
    )



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate confusion and brickle bedside stories with dialogue and repetition."
    )
    parser.add_argument("--scene", choices=sorted(SCENES), default=None)
    parser.add_argument("--problem", choices=sorted(PROBLEMS), default=None)
    parser.add_argument("--method", choices=sorted(METHODS), default=None)
    parser.add_argument("--hero", default=None)
    parser.add_argument("--hero-kind", choices=sorted(HERO_NAMES), default=None)
    parser.add_argument("--helper", choices=sorted(HELPERS), default=None)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser



def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    combo = rng.choice(_matching_combos(args))
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



def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        _print_qa(sample)



def _emit_asp_listing() -> None:
    for scene_key, problem_key, method_key in sorted(asp_valid_combos()):
        print(f"{scene_key}\t{problem_key}\t{method_key}")



def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

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

        samples: list[StorySample] = []
        if args.all:
            combos = _matching_combos(args)
            for index, combo in enumerate(combos, 1):
                samples.append(generate(_params_from_combo(args, combo, index)))
        else:
            count = max(1, args.n)
            for index in range(count):
                rng = random.Random(args.seed + index)
                samples.append(generate(resolve_params(args, rng, index)))

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for index, sample in enumerate(samples, 1):
            header = ""
            if args.all:
                p = sample.params
                header = f"### {p.scene} / {p.problem} / {p.method}"
            elif len(samples) > 1:
                header = f"### variant {index}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index != len(samples):
                print("\n" + "=" * 72 + "\n")

        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2



if __name__ == "__main__":
    raise SystemExit(main())
