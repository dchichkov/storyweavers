#!/usr/bin/env python3
"""A varied nursery-rhyme StoryWorld about a definitive toss and sharing."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    setting: str = "the nursery"
    first_name: str = "Mina"
    second_name: str = "Ned"
    toy: str = "the red ball"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    premise: str
    trouble: str
    failed: str
    clue: str
    plan: str
    jobs: tuple[str, str]
    result: str
    lesson: str
    ending: str


SETTINGS = {"the nursery": True, "the playroom": True, "the garden patch": False}
NAMES = ["Mina", "Ned", "Lena", "Ollie", "Pia", "Rory", "Tessa", "Finn"]
TOYS = [("the red ball", "ball"), ("the blue hoop", "hoop"),
        ("the bright ribbon", "ribbon"), ("the soft kite", "kite")]

SCENARIOS = [
    Scenario("chalk-gates", "drew two chalk gates for a passing game",
             "Both rushed to guard the same gate, leaving the other empty.",
             "racing between both gates made the game stop",
             "two chalk arrows pointed in opposite directions, one for each friend",
             "stand at separate gates and toss only after hearing 'ready'",
             ("brushed one line clear and watched the near gate", "stood by the far arrow and called the count"),
             "The toss crossed both arrows, and neither gate was left alone.",
             "friends can share a game by taking different, equally useful places",
             "the toy rested between two bright arrows while four chalky hands met in a clap"),
    Scenario("block-tower", "built a squat block tower as a target",
             "One hard throw scattered the tower and sent a block under a shelf.",
             "throwing harder pushed the blocks farther apart",
             "the blocks still standing were the wide ones at the bottom",
             "rebuild a broad tower, then share one soft practice toss",
             ("sorted broad blocks into a steady base", "fetched the runaway block and marked a safe line"),
             "Their gentle toss tapped the top block without toppling the base.",
             "sharing includes caring for the game and its things",
             "one yellow block wobbled, settled, and shone above their joined shadows"),
    Scenario("rhyme-cards", "laid out picture cards and aimed for a matching rhyme",
             "They argued over whether moon matched spoon or star matched jar.",
             "shouting both answers made it impossible to hear either rhyme",
             "each card had a colored dot pairing it with one other card",
             "take turns reading a pair and toss together on the final word",
             ("found the blue-dot card and spoke its first word", "found its partner and waited to answer"),
             "They called 'moon, spoon,' and the toss landed beside the pair.",
             "taking turns can make two ideas part of one answer",
             "the moon and spoon cards lay together beneath a silver arc"),
    Scenario("cushion-river", "made a pretend river with cushion islands",
             "The toy landed in the middle, beyond either bank.",
             "stretching from one bank wrinkled the river and moved it farther away",
             "an opposite cushion was close enough to receive a careful toss",
             "pass the toy from bank to island to bank",
             ("held the first island still with both knees", "slid the far cushion into line and opened both hands"),
             "The final toss cleared the blue cloth, which stayed smooth and dry.",
             "each friend can protect one part of a shared path",
             "three dry cushions curved across the blue river like stepping-stones"),
    Scenario("bell-count", "hung a bell and invented a rhyme for each pass",
             "They tossed too quickly, and the bell rang before anyone was ready.",
             "trying to beat the bell caused two hurried misses",
             "the bell rope swung four times while their rhyme had three beats",
             "prepare for three beats and make the definitive toss on four",
             ("tapped three quiet beats", "watched the toy and called 'toss' on the fourth"),
             "The toy arrived with the bell's clear ting on the final beat.",
             "a shared rhythm works when friends listen as carefully as they speak",
             "the bell rope became still as the last bright note floated over the toy"),
    Scenario("missing-basket", "decorated a basket as the toy's shared home",
             "The basket vanished while they argued over who would keep the toy first.",
             "accusing each other wasted time and made both clutch the toy",
             "paper stars led behind a curtain where the basket had rolled",
             "follow the clues and give the toy a home both could use",
             ("lifted the curtain and gathered the stars", "pulled the basket free and checked its handle"),
             "They tossed the toy into the basket, ready for either friend tomorrow.",
             "a shared home can prevent a quarrel before it begins",
             "two name tags dangled from one basket handle beside the tucked-in toy"),
    Scenario("sleepy-corner", "promised a quiet game near resting dolls",
             "Their excited calls tipped the smallest doll from its pillow.",
             "whispering while tossing wildly still bumped the pillow",
             "a feather drifted safely only when their hands moved low and slowly",
             "use soft voices and keep every toss below the pillows",
             ("made a low starting circle away from the dolls", "cushioned the landing spot and answered softly"),
             "The toy made one quiet arc, and every pretend sleeper stayed snug.",
             "sharing fun means noticing who needs peace nearby",
             "a feather lay unruffled beside the pillows as the friends tiptoed away"),
    Scenario("windy-pennant", "set a tossing line beneath a paper pennant",
             "A gust wrapped the pennant around the toy and tugged it toward a hedge.",
             "pulling opposite ends tightened the twist",
             "the knot loosened whenever both ends moved toward the middle",
             "step inward together, free the toy, and face away from the wind",
             ("shielded the loose end", "worked the twist backward without yanking"),
             "The freed toy sailed toward the sheltered line instead of the hedge.",
             "cooperation can mean easing a problem before pulling ahead",
             "the pennant fluttered free above a toy cupped safely in two hands"),
    Scenario("turn-token", "made a gold token to show whose turn came next",
             "The token slipped under a rug, and both claimed the next toss.",
             "arguing from memory turned a small doubt into a quarrel",
             "one gold edge peeked out beside the last tossing mark",
             "recover the token, finish the paused turn, then pass both items",
             ("rolled back the rug without moving the line", "picked up the token and admitted whose turn had paused"),
             "One fair toss finished the old turn, and the token changed hands with it.",
             "honesty makes taking turns easier than winning an argument",
             "the gold token lay on an open palm while the toy waited at the next mark"),
    Scenario("window-light", "aimed tosses through a square of sunlight",
             "A cloud moved the bright square, and one friend called a fair toss a miss.",
             "repeating the toss at the old mark proved nothing as the light drifted",
             "the sun patch had crossed three floorboards in one minute",
             "mark a fixed yarn square and judge every turn by the same boundary",
             ("laid two sides of the yarn square straight", "finished the corners and invited another try"),
             "The toss crossed the fixed square, giving both friends one clear rule.",
             "fair sharing needs rules that do not change for one person",
             "the yarn square glowed after the patch of sunlight wandered away"),
    Scenario("garden-seeds", "placed empty seed cups as targets",
             "A missed toss knocked water toward the seed packets.",
             "chasing the toy first let the stream creep closer to the seeds",
             "a folded garden mat could block the water",
             "save the seeds, dry the ground, then resume farther away",
             ("raised the packets and held the mat like a dam", "mopped the stream and moved the tossing line"),
             "Only after the seeds were dry did they toss into the widest cup.",
             "friends pause a game when something living needs care",
             "three dry seed packets stood beside a cup holding the toy like a flower"),
    Scenario("friendship-patch", "made a friendship patch for ten shared tosses",
             "The paper patch tore when both friends reached for the prize.",
             "hiding one half each left the prize broken and both faces glum",
             "the torn star edges still matched like puzzle pieces",
             "mend the patch and award it to their friendship, not one winner",
             ("lined up the torn stars and held them flat", "taped across both halves and smoothed them"),
             "Their final toss completed the game, and they pinned the whole patch above it.",
             "some prizes belong to what friends made together",
             "the mended patch hung over two stools with its silver crack visible"),
]

OPENINGS = [
    "Morning light found {a} and {b} making a game in {setting}.",
    "In {setting}, {a} had an idea that made {b}'s eyes brighten.",
    "A tap, a clap, and a whispered rhyme began playtime in {setting}.",
    "Before the tidy-up bell, {a} and {b} chose one last game in {setting}.",
    "There was room for two friends and one favorite toy in {setting}.",
    "Rain or shine, {a} and {b} invented games in {setting}.",
    "A small challenge waited beside {toy} in {setting}.",
    "{a} and {b} arrived in {setting} with busy hands and a shared plan.",
]
REACTIONS = [
    "'This is not a sharing game yet,' {a} admitted.",
    "{b} folded both hands. 'Let us find what changed.'",
    "For one uncomfortable moment, each wanted the other to give in.",
    "'Pause the toss,' {b} said. 'A fair game can wait for a plan.'",
    "{a} nearly grabbed again, then noticed {b}'s disappointed face.",
    "The rhyme stopped in the middle; their friendship needed attention.",
    "Neither child laughed. Winning alone suddenly looked very small.",
    "'We can mend this without blaming,' {a} said.",
]
REFRAINS = [
    "One for you and one for me; shared in friendship, fair as can be.",
    "Ready, steady, hands in view; I share the toss, then so do you.",
    "Near or far, low or high; friends send kindness through the sky.",
    "Count one, count two, then let it go; sharing helps our friendship grow.",
    "Pass with care and call my name; two kind turns can make one game.",
    "Toss it gently, catch it light; taking turns can set things right.",
    "Mine for a moment, yours for a while; back comes the toy, along comes a smile.",
    "Clap for the catch and cheer for the try; friends make room as turns go by.",
]
TURNS = [
    "The clue changed their question from 'Who gets it?' to 'How can both help?'",
    "That clue was the definitive turn: it gave them one problem to solve together.",
    "Instead of choosing an owner, they chose two jobs.",
    "The quarrel loosened when they tested the clue side by side.",
    "Then {a} offered the first turn to {b}, and the game felt shared.",
    "They named what had gone wrong before touching the toy again.",
    "A fair toss would be the proof, but first they had to repair the game.",
    "They counted jobs, not points, and found useful work for both.",
]
TOY_ACTIONS = {"the red ball": "a low underhand toss", "the blue hoop": "a careful two-handed toss",
               "the bright ribbon": "a light toss that let its tail float", "the soft kite": "a gentle upward toss into clear space"}


def generate_world(p: StoryParams) -> World:
    world = World(p.setting)
    a = world.add(Entity("A", "character", p.first_name))
    b = world.add(Entity("B", "character", p.second_name))
    toy = world.add(Entity("T", "thing", p.toy))
    seed = abs(p.seed or 0)
    si = seed % 12
    oi = (seed // 12) % 8
    ri = (seed // 96) % 8
    fi = (seed // 768) % 8
    scene = SCENARIOS[si]
    rhyme = REFRAINS[fi]
    world.say(OPENINGS[oi].format(a=a.label, b=b.label, setting=p.setting, toy=toy.label))
    world.say(f"Their game used {toy.label}. Together, the friends {scene.premise}.")
    world.say(f"Their nursery rhyme began, '{rhyme}'")
    world.para()
    world.say(scene.trouble)
    world.say(REACTIONS[ri].format(a=a.label, b=b.label))
    world.say(f"At first, {a.label} tried alone, but {scene.failed}.")
    world.say(f"Then {b.label} noticed a clue: {scene.clue}.")
    world.para()
    world.say(TURNS[(oi + ri) % 8].format(a=a.label, b=b.label))
    world.say(f"Their plan was to {scene.plan}.")
    world.say(f"{a.label} {scene.jobs[0]}, while {b.label} {scene.jobs[1]}.")
    world.say(f"Together they made {TOY_ACTIONS[toy.label]}. {scene.result}")
    world.para()
    world.say(f"They sang again: '{rhyme}'")
    world.say("The definitive toss did not decide a winner; it proved they could share.")
    world.say(f"{b.label} said their lesson was that {scene.lesson}.")
    world.say(f"At the end, {scene.ending}.")
    a.memes.update(friendship=1.0, sharing=1.0)
    b.memes.update(friendship=1.0, sharing=1.0)
    toy.meters.update(shared=1.0, tossed=1.0)
    world.facts.update(first=a.label, second=b.label, toy=toy.label, scenario=scene.key,
                       trouble=scene.trouble, failed=scene.failed, clue=scene.clue, plan=scene.plan,
                       first_job=scene.jobs[0], second_job=scene.jobs[1], result=scene.result,
                       lesson=scene.lesson, ending=scene.ending, rhyme=rhyme, shared=True, tossed=True)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    trouble = str(f["trouble"])
    return [
        QAItem(question=f"What interrupted {f['first']} and {f['second']}'s game?",
               answer=f"Their game was interrupted when {trouble[0].lower() + trouble[1:]} The trouble stopped their shared play."),
        QAItem(question="What clue helped them choose a better plan?",
               answer=f"They noticed that {f['clue']}. That clue helped them cooperate instead of compete."),
        QAItem(question="How did the friends divide the work?",
               answer=f"{f['first']} {f['first_job']}, while {f['second']} {f['second_job']}. Both jobs prepared the final toss."),
        QAItem(question="Why was the final toss definitive?",
               answer=f"It proved that the friends could share {f['toy']} fairly. {f['result']}"),
        QAItem(question="What lesson and ending image closed the story?",
               answer=f"They learned that {f['lesson']}. In the final image, {f['ending']}."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is friendship?", answer="Friendship is a caring relationship in which people listen, help, and enjoy time together."),
        QAItem(question="What does sharing mean?", answer="Sharing means making room for another person to use or enjoy something too."),
        QAItem(question="What is a toss?", answer="A toss is a light throw. A safe toss uses clear space and a receiver who is ready."),
        QAItem(question="What does definitive mean?", answer="Definitive means clear and decisive. It can prove that an important change truly happened."),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [f"Write a nursery-rhyme story about {f['first']} and {f['second']} sharing {f['toy']}.",
            f"Tell a friendship tale in {world.setting} where the clue is that {f['clue']}.",
            "Create a child-friendly story in which a definitive toss proves two friends can share."]


ASP_RULES = r"""
friend_pair(A,B) :- friend(A,B), A < B.
shared_story(A,B,T) :- friend_pair(A,B), shares(A,T), shares(B,T), toy(T).
definitive_turn(T) :- tossed(T), shared_story(_,_,T).
#show friend_pair/2.
#show shared_story/3.
#show definitive_turn/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for a, b in [("mina", "ned"), ("lena", "ollie"), ("pia", "rory")]:
        lines.extend([asp.fact("friend", a, b), asp.fact("friend", b, a)])
    for label, toy in TOYS:
        lines.extend([asp.fact("toy", toy), asp.fact("label", toy, label),
                      asp.fact("shares", "mina", toy), asp.fact("shares", "ned", toy), asp.fact("tossed", toy)])
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    atoms = asp.atoms(asp.one_model(asp_program("#show definitive_turn/1.")), "definitive_turn")
    print("OK: ASP program found a definitive shared toss." if atoms else "MISMATCH: no definitive toss.")
    return 0 if atoms else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--setting", choices=sorted(SETTINGS)); ap.add_argument("--first-name"); ap.add_argument("--second-name")
    ap.add_argument("--toy", choices=[t[0] for t in TOYS]); ap.add_argument("-n", type=int, default=1); ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true"); ap.add_argument("--trace", action="store_true"); ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true"); ap.add_argument("--asp", action="store_true"); ap.add_argument("--verify", action="store_true"); ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    first = args.first_name or rng.choice(NAMES)
    second = args.second_name or rng.choice([n for n in NAMES if n != first])
    if first == second:
        raise StoryError("The two friends must be different children.")
    return StoryParams(setting=args.setting or rng.choice(sorted(SETTINGS)), first_name=first, second_name=second,
                       toy=args.toy or rng.choice([t[0] for t in TOYS]), seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world),
                       story_qa=story_qa(world), world_qa=world_qa(world), world=world)


CURATED = [StoryParams("the nursery", "Mina", "Ned", "the red ball", 12),
           StoryParams("the playroom", "Lena", "Ollie", "the blue hoop", 49),
           StoryParams("the garden patch", "Pia", "Rory", "the bright ribbon", 83)]


def emit(sample: StorySample, trace: bool, qa: bool, header: str = "") -> None:
    if header: print(header)
    print(sample.story)
    if trace and sample.world:
        print(f"\n--- world model state ---\nscenario={sample.world.facts['scenario']} shared=True tossed=True")
    if qa:
        for i, item in enumerate(sample.story_qa, 1): print(f"Q{i}: {item.question}\nA{i}: {item.answer}")
        for i, item in enumerate(sample.world_qa, 1): print(f"W{i}: {item.question}\nA{i}: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp: print(asp_program("#show friend_pair/2. #show shared_story/3. #show definitive_turn/1.")); return
    if args.verify: raise SystemExit(asp_verify())
    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base + i)); p.seed = base + i; samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], ensure_ascii=False, indent=2)); return
    for i, sample in enumerate(samples):
        emit(sample, args.trace, args.qa, f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples): print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
