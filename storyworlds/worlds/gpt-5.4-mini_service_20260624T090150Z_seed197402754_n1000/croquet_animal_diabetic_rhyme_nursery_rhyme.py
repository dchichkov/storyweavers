#!/usr/bin/env python3
"""A varied, respectful nursery-rhyme StoryWorld about diabetes and croquet."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StorySample  # noqa: E402


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Milo"
    animal: str = "bunny"
    helper: str = "mama"
    setting: str = "the green"
    rhyme_word: str = "croquet"
    scenario: str = "low_alert"
    telling_mode: str = "bell"
    variant: int = 0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in ANIMALS:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"mama", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"papa", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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


@dataclass(frozen=True)
class Scenario:
    key: str
    title: str
    premise: str
    problem: str
    clue: str
    bad_idea: str
    action: str
    dialogue: str
    play: str
    result: str
    lesson: str
    ending: str


ANIMALS = ("bunny", "cat", "dog", "duck", "bear", "mouse")
HELPERS = ("mama", "papa", "mom", "dad")
SETTINGS = ("the green", "the lawn", "the sunny yard")
NAMES = ("Milo", "Nina", "Pip", "Tess")
MODES = ("bell", "question", "score", "whisper", "steps", "chorus", "clock", "mallet")

SCENARIOS = (
    Scenario("low_alert", "chiming pocket", "the first hoop waited beside clover", "a glucose alert chimed before the opening turn", "the reading and a shaky feeling agreed", "swing fast and hope it passed", "followed the personal care plan with the helper, used the planned fast-acting carbohydrate, waited, and rechecked", "A chime is a clue, so we stop and review", "sent the red ball through two hoops with one measured tap", "the next check reached the care-plan range, so play safely began", "noticing a low early protects later fun", "The red ball rested beyond the clover hoop while the care pouch hung zipped on its peg."),
    Scenario("high_reading", "patient wicket", "a striped wicket leaned beneath the noon flag", "the pre-game check was above the range in the care plan", "the number showed that the start needed to wait", "copy another player's medicine or invent a dose", "reviewed the written instructions, drank water as the plan allowed, and rested in shade", "No borrowed dose and no hurried race; our own care plan sets the pace", "banked the yellow ball off the boundary after being cleared to return", "the written plan and helper decided when play could resume", "a high reading calls for the person's plan and a trusted adult", "The yellow ball clicked through the striped wicket as the noon flag softened in the breeze."),
    Scenario("missing_strip", "empty meter pocket", "the hoops formed a spiral like a snail", "the meter case opened with its strip pocket empty", "a BACKUP tab pointed toward the clubhouse cupboard", "pretend a check had happened", "paused while the helper fetched labeled backup supplies and completed the usual check", "We never make up what a meter should say; we fetch what we need before starting our play", "threaded the green ball around the spiral", "honest teamwork solved the supply problem before the first swing", "preparation includes checking health supplies", "The strip wrapper went into the bin, and the green ball gleamed beside the last spiral hoop."),
    Scenario("falling_arrow", "arrow before the hill", "three hoops climbed toward a paper windmill", "the continuous glucose monitor showed a downward arrow", "the trend was changing although the player felt eager", "race uphill before the number changed", "studied the trend and followed the personal plan before deciding about play", "An arrow that falls deserves a pause; look at the trend and follow its cause", "guided the blue ball down the slope with a soft backswing", "attention to the trend prevented a risky dash", "devices give clues while the individual plan guides action", "The paper windmill turned once while the blue ball waited safely below the hill."),
    Scenario("loose_sensor", "snagged ribbon", "festival ribbons fluttered from every hoop", "one ribbon caught the glucose sensor patch", "the loose corner explained the sudden signal gap", "press buttons until a convenient number appeared", "protected the site and used the established backup-check steps", "A missing signal is not a number to choose; ask for help and use backup clues", "rolled the purple ball beneath ribbons tied farther away", "the course changed so ribbons could not brush the device", "equipment problems belong with the normal backup plan", "The ribbons streamed clear of the patch while the purple ball nestled under the last hoop."),
    Scenario("reserved_snack", "picnic mix-up", "a picnic blanket became the scoreboard", "a teammate offered the labeled emergency snack as picnic food", "the label said it belonged in the diabetes care kit", "stay silent and hope enough remained", "explained the label, returned the unopened portion, and asked the helper to confirm the kit was complete", "Sharing is grand, but labels explain: this care-kit snack must ready remain", "gave every teammate a turn at the silver bell hoop", "friends shared other crackers and kept the care supply available", "kindness includes respecting health supplies", "Crackers circled the scoreboard, and the labeled pouch stayed closed beneath the pear tree."),
    Scenario("hot_day", "shady half-course", "sunlight flashed on six hoops at noon", "the heat made the full course tiring sooner than expected", "warm ears and an empty water cup said to slow down", "finish every wicket before resting", "moved half the course into shade, refilled water, checked according to the care plan, and rested often", "Shade, sip, check; then choose what comes next", "played a shorter round with one shaded hoop per partner", "adapting the course kept croquet comfortable", "activities can change while usual diabetes care continues", "Cool pawprints crossed the shade, and a water bead shone on the final wooden hoop."),
    Scenario("body_clue", "quiet cheer", "toy animals lined the path to a bell hoop", "the cheers hid a faint hungry, shaky feeling", "quiet made the body clue easier to notice", "hide the feeling to avoid disappointing friends", "used the agreed pause signal, checked, and followed the result-specific plan", "A brave player can stop and say: my body has news before more croquet", "returned when ready and tapped the ball as friends cheered softly", "speaking up made the noisy match kinder and safer", "symptoms should be reported and checked, not guessed about", "The toy crowd held QUIET signs while the ball rang the bell hoop once."),
    Scenario("wet_meter", "sprinkler surprise", "the course curved beside ticking sprinklers", "sprinkler drops reached the open meter case", "speckles on the lid showed the device might be wet", "shake it and trust any number", "closed the case and used dry backup equipment according to its instructions", "If gear gets wet, don't guess what is true; keep it dry and let an adult help you", "sent the orange ball along the dry course", "the team protected both garden and health equipment", "medical devices should be used as directed", "The sprinkler ticked away from the towel where the orange ball and backup case sat together."),
    Scenario("inclusion", "captain's mistake", "two teams chose ribbons for doubles", "a captain assumed a diabetic animal could not join", "the player had supplies, a plan, and practiced skill", "accept the sideline without correcting the assumption", "explained that diabetes needs planning, not exclusion, and taught the agreed pause signal", "Diabetic is one health word, not all that you see; plan for my care, then please play with me", "called the angles while a partner struck the final ball", "the captain apologized and made the rules fair", "children with diabetes belong in games with appropriate support", "Equal team ribbons fluttered over the crossed mallets at the winner's peg."),
    Scenario("schedule_change", "late tournament", "a chalk clock announced a morning match", "rain delayed play beyond the planned time", "the changed clock affected the usual food, check, and activity schedule", "follow the old timetable without telling anyone", "reviewed the new schedule and followed the established plan before choosing a start time", "When clocks rearrange, notice the change; check with your helper before taking range", "helped dry the hoops and opened the delayed match", "communication kept the changed routine clear", "unexpected timing is a reason to consult the care plan", "The chalk hands showed the new start while raindrops sparkled on the dried hoops."),
    Scenario("curious_friend", "question by the peg", "practice ended at a moon-painted peg", "a teammate asked clumsily why the care kit was needed", "the question came from uncertainty, not cruelty", "turn the question into a joke about a body", "answered only what felt comfortable while the helper reminded everyone to respect privacy", "Ask with respect, and accept not today; a friend owns their story while friends croquet", "invited the teammate to score as the moon ball crossed the line", "respectful listening replaced awkward guessing", "curiosity should come with consent and privacy", "The moon ball touched the starry peg, and the private care kit stayed quietly beneath the bench."),
)
SCENARIO_BY_KEY = {scenario.key: scenario for scenario in SCENARIOS}

OPENINGS = (
    "Tap-tap, morning map: {name} carried a mallet to {setting}.",
    "Under a clean blue sky, {name} found a croquet course ready and new.",
    "Hoop by hoop and peg by peg, a game-day rhyme danced over {setting}.",
    "Wooden balls made a colorful row while {name} planned where each should go.",
    "Before the first bell could tinkle or ring, {name} checked the course and every small thing.",
    "A nursery-rhyme match was ready to begin, with careful plans beside hopes of a win.",
)
REFRAINS = {
    "bell": "Ding went the bell: facts first, then play; care helped the game find its way.",
    "question": "What should we do before playing away? Pause, find the facts, choose the safe way.",
    "score": "The scoreboard marked no hurry, no race; good information would set the pace.",
    "whisper": "First came a whisper, steady and clear; later came clapping that all friends could hear.",
    "steps": "One: stop. Two: tell. Three: follow the plan. Those were the steps before play began.",
    "chorus": "The friends sang low: we listen, we learn; care comes first, then each gets a turn.",
    "clock": "Weather may wander and clocks may stray; the care plan helps shape a safer day.",
    "mallet": "Mallet down, voices calm; facts and a helper keep play from harm.",
}
TRANSITIONS = (
    "That shortcut would have hidden the clue.", "For a moment, the quickest idea sounded grand.",
    "The ball could wait; a wiser choice mattered more.", "Winning seemed less important than understanding.",
    "A hurried guess knocked at the plan's door, but nobody let it in.", "The first idea was speedy, but speed was not evidence.",
)
MORAL_LEADS = (
    "Beneath the last notes of the rhyme, {name} understood", "As the mallets were stacked, {name} remembered",
    "The smallest hoop carried the biggest lesson:", "On the chalkboard, the team wrote what the match proved:",
    "One line from the croquet song remained:", "Long after the score was forgotten, everyone knew",
)


def build_world(params: StoryParams) -> World:
    world = World(params)
    child = world.add(Entity(id=params.name, kind="character", type=params.animal, label=params.name, meters={"steadiness": 1.0}, memes={"joy": 0.8, "confidence": 0.7}))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=params.helper, meters={"care": 1.0}, memes={"care": 1.0}))
    world.add(Entity(id="croquet_set", label="croquet set", phrase="a wooden croquet set"))
    world.add(Entity(id="care_kit", label="diabetes care kit", phrase="a labeled diabetes care kit", owner=child.id))
    world.facts.update(child=child, helper=helper, has_diabetes=True)
    return world


def pick(options: tuple[str, ...], params: StoryParams, salt: int) -> str:
    return random.Random((params.variant * 1_000_003) ^ (salt * 97_409)).choice(options)


def simulate(world: World) -> World:
    p = world.params
    child, helper, case = world.get(p.name), world.get("Helper"), SCENARIO_BY_KEY[p.scenario]
    world.say(pick(OPENINGS, p, 1).format(name=child.id, setting=p.setting))
    world.say(f"{child.id}, a lively little {child.type}, loved animal games, especially croquet. {child.id} had diabetes; the word diabetic named one health fact, never the whole of who {child.pronoun()} were.")
    world.say(f"{child.pronoun('possessive').title()} labeled care kit and personal care plan waited beside {helper.label}, ready if needed.")
    world.say(f"Today, {case.premise}.")
    world.para()
    world.say(f"Then {case.problem}. The important clue was that {case.clue}.")
    world.say(pick(TRANSITIONS, p, 2))
    world.say(f"It would not be safe to {case.bad_idea}.")
    world.para()
    world.say(f"{helper.label.title()} listened while {child.id} explained the clue. Together they {case.action}.")
    world.say(f"'{case.dialogue},' {helper.label} said. {REFRAINS[p.telling_mode]}")
    world.para()
    world.say(f"Because they used the clue instead of a guess, {case.result}. Back at croquet, {child.id} {case.play}.")
    world.say(f"{pick(MORAL_LEADS, p, 3).format(name=child.id)} {case.lesson}.")
    world.say(case.ending)
    world.fired.update({"paused", "helper_told", "care_plan_followed", "resolved", "included"})
    child.memes.update(joy=1.2, confidence=0.9)
    world.facts.update(scenario=case.key, incident=case.problem, clue=case.clue, care_action=case.action, result=case.result, lesson=case.lesson, ending=case.ending, used_personal_plan=True, improvised_dose=False, included_in_play=True)
    return world


def generation_prompts(world: World) -> list[str]:
    p, case = world.params, SCENARIO_BY_KEY[world.params.scenario]
    return [
        f"Write a child-friendly nursery rhyme about {p.name}, a {p.animal} with diabetes, solving the {case.title} problem during croquet.",
        f"Tell a gentle animal rhyme where the clue '{case.clue}' and a personal care plan guide a safe choice.",
        f"Write an inclusive croquet story with dialogue, a causal resolution, and the final image: {case.ending}",
    ]


def story_qa(world: World) -> list[QAItem]:
    p, case = world.params, SCENARIO_BY_KEY[world.params.scenario]
    return [
        QAItem(question=f"What interrupted {p.name}'s croquet game?", answer=f"The game paused because {case.problem}. That began the {case.title} problem."),
        QAItem(question=f"What clue did {p.name} notice?", answer=f"{p.name} noticed that {case.clue}. The clue gave {p.name} and {p.helper} evidence instead of a guess."),
        QAItem(question=f"How did {p.name} and {p.helper} respond?", answer=f"They {case.action}. They used the established care plan rather than improvising treatment."),
        QAItem(question="Why was the tempting first idea rejected?", answer=f"It would not have been safe to {case.bad_idea}. Speed and guessing were not substitutes for evidence and a personal care plan."),
        QAItem(question=f"How was the {case.title} problem resolved, and what final image proves it?", answer=f"The result was that {case.result}. {case.ending} The image shows the player remained part of the game."),
        QAItem(question="What did the players learn?", answer=f"They learned that {case.lesson}. Diabetes was one manageable part of the player's life, not the player's identity."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="Can a child with diabetes take part in games and sports?", answer="Yes. Children with diabetes can participate with their usual supplies, individual care plan, and appropriate adult support."),
        QAItem(question="Should every unexpected glucose reading be treated with a snack?", answer="No. The response depends on the reading, symptoms, device guidance, and that person's care plan; a trusted adult or clinician should guide care rather than a story."),
        QAItem(question="What does glucose-monitoring equipment do?", answer="It provides information about glucose levels or trends, helping a person follow an individual diabetes care plan."),
        QAItem(question="What should a child do when diabetes equipment fails or a reading is concerning?", answer="The child should pause, tell a trusted adult, and follow the established backup or care plan. They should not guess a dose or copy somebody else's treatment."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)), "", "== Story QA =="]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.extend(("", "== World QA =="))
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


ASP_RULES = """child(X) :- animal(X).
supported(X) :- child(X), has_diabetes(X), helper_told(X), care_plan_followed(X).
included(X) :- supported(X), cleared_by_plan(X), croquet_player(X).
"""


def asp_facts(params: Optional[StoryParams] = None) -> str:
    import asp
    atom = (params or StoryParams()).name.lower()
    return "\n".join(asp.fact(predicate, atom) for predicate in ("animal", "has_diabetes", "helper_told", "care_plan_followed", "cleared_by_plan", "croquet_player"))


def asp_program(show: str, params: Optional[StoryParams] = None) -> str:
    return f"{asp_facts(params)}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    atoms = set(asp.atoms(asp.one_model(asp_program("#show included/1.")), "included"))
    ok = bool(atoms)
    print("OK: ASP twin confirms supported, plan-cleared inclusion." if ok else "ASP verification failed.")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Varied nursery-rhyme croquet StoryWorld.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(seed=args.seed, name=args.name or rng.choice(NAMES), animal=args.animal or rng.choice(ANIMALS), helper=args.helper or rng.choice(HELPERS), setting=args.setting or rng.choice(SETTINGS), scenario=rng.choice(SCENARIOS).key, telling_mode=rng.choice(MODES), variant=rng.randrange(1, 2**31))


def generate(params: StoryParams) -> StorySample:
    world = simulate(build_world(params))
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world is not None:
        print(f"\n--- trace ---\nfacts: {sample.world.facts}")
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show included/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(StoryParams(name="Milo", animal="bunny", helper="mama", setting="the green", scenario=key, telling_mode=mode, variant=i + 11)) for i, (key, mode) in enumerate((("low_alert", "bell"), ("inclusion", "chorus"), ("wet_meter", "question")))]
    else:
        samples = [generate(resolve_params(args, random.Random(base_seed + i))) for i in range(args.n)]
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
