#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

from storyworlds.results import QAItem, StoryError, StorySample  # eager import


ASP_RULES = r"""
mechanism(bridge_lift).
feature(friendship).
feature(cautionary).
feature(twist).
style(mystery).

safe_story :- mechanism(bridge_lift), feature(friendship), feature(cautionary), feature(twist), style(mystery).
#show safe_story/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Lina"
    friend: str = "Moss"
    object_name: str = "the brass whistle"
    place: str = "the river gate"
    machine: str = "bridge lift"
    setting: str = "the old canal lock"
    mood: str = "curious"


@dataclass
class Character:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, delta: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + delta

    def add_meme(self, key: str, delta: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + delta


@dataclass
class ObjectThing:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, delta: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + delta

    def add_meme(self, key: str, delta: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + delta


@dataclass
class World:
    params: StoryParams
    characters: dict[str, Character] = field(default_factory=dict)
    objects: dict[str, ObjectThing] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    def say(self, line: str) -> None:
        self.trace.append(line)

    def add_character(self, ch: Character) -> Character:
        self.characters[ch.name] = ch
        return ch

    def add_object(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.name] = obj
        return obj

    def render(self) -> str:
        return "\n\n".join(self.trace)


SCENARIOS = [
    {
        "title": "the missing key in the lock house",
        "opening": "At dusk, {name} and {friend} reached {setting} with {object_name} tucked in a pocket.",
        "mystery": "A lantern was burning inside, but the gate to {place} stood open and nobody was on duty.",
        "clue": "Fresh mud on the floor pointed toward the little gear room, and one tooth on the lift wheel was marked with chalk.",
        "mistake": "{name} almost pulled the wrong lever, because the chalk mark looked like a shortcut.",
        "dialogue": "'Let's not guess,' {friend} said. '{object_name} only tells us someone wanted attention, not action.'",
        "action": "{name} checked the mechanism with a careful flashlight while {friend} listened for the click of the hidden latch.",
        "twist": "Behind the wheel, they found a sleepy kitten guarding a tin of bolts, and the missing key was tied to its collar.",
        "resolution": "The kitten was carried to warmth, the bolts were sorted by size, and the lift gate closed exactly as it should.",
        "ending": "By nightfall, the river gate sat safe and quiet, with the brass whistle hanging beside a repaired wheel.",
        "lesson": "friendship means solving a mystery without rushing past what might be small and scared",
    },
    {
        "title": "the silent bell under the bridge",
        "opening": "When the moon rose, {name} and {friend} crossed {setting} to inspect {place}.",
        "mystery": "The warning bell should have rung, yet the only sound was water tapping the stone like tiny fingers.",
        "clue": "A wet ribbon snagged on the bell rope, and the rope led down to the lower gear chamber.",
        "mistake": "{name} started to tug the ribbon free, but the floorboards shivered under one foot.",
        "dialogue": "'That floor is telling us to slow down,' {friend} whispered. 'A cautionary mystery is still a mystery.'",
        "action": "{name} asked {friend} to hold the lantern while they used the hook pole to lift the ribbon from a safe spot.",
        "twist": "The ribbon belonged to the town baker, who had tied it there to mark a leak before anyone slipped.",
        "resolution": "They found the leak, shut the valve, and left a note so the baker would know the warning had been understood.",
        "ending": "The bell rang again over the bridge, and the moonlight flashed on dry stones instead of puddles.",
        "lesson": "careful questions can turn a warning into help",
    },
    {
        "title": "the wax seal in the gear box",
        "opening": "At the old canal lock, {name} noticed a red wax seal on {machine} and called {friend} over at once.",
        "mystery": "No one in the watchhouse admitted placing it there, and the lock had begun to shiver in the wind.",
        "clue": "The seal carried a tiny stamp shaped like a fish, the same shape carved on the tool shed key.",
        "mistake": "{name} nearly broke the seal open, then remembered that some secrets are warnings, not invitations.",
        "dialogue": "'We should ask who owns the stamp before we open anything,' {friend} said.",
        "action": "{name} and {friend} followed the fish stamp to the tool shed and found the gardener counting lost labels.",
        "twist": "The gardener had sealed the box to keep out rain, but a prankster had moved the label and made the whole lock seem haunted.",
        "resolution": "Together they dried the box, returned the label, and set the lock wheel straight before the next boat arrived.",
        "ending": "The canal water settled smooth again, and the fish stamp was tucked safely into the gardener's apron pocket.",
        "lesson": "a mystery can have a plain answer, but caution keeps the answer from breaking",
    },
    {
        "title": "the lantern code at the towpath",
        "opening": "{name} and {friend} walked the towpath with {object_name} and a notebook full of questions.",
        "mystery": "Three lanterns blinked in a pattern that matched the mechanism room's maintenance chart.",
        "clue": "Each blink landed where the chart showed a different switch, as if someone were asking for help in code.",
        "mistake": "{name} wanted to follow the code alone, but the reeds hid a muddy drop beside the path.",
        "dialogue": "'Two friends see more than one,' {friend} said, stepping back from the edge.",
        "action": "{name} copied the pattern while {friend} ran for the lock keeper and described the blinking order exactly.",
        "twist": "The lanterns were not a warning at all; they were the lock keeper's clever way of teaching a new helper the switches.",
        "resolution": "The new helper arrived, the switches were matched correctly, and the towpath lights all stayed steady.",
        "ending": "The final lantern glowed like a small white eye over the water, calm and clear.",
        "lesson": "friendship can slow a hasty guess into a wiser one",
    },
    {
        "title": "the scratch on the brass panel",
        "opening": "Near {place}, {name} found a scratch across {object_name} and felt the mystery begin.",
        "mystery": "The scratch curved like a river bend, and the mechanism would not open when the handle turned.",
        "clue": "A bit of blue thread clung to the panel, the same color as {friend}'s scarf.",
        "mistake": "{name} suspected {friend} at first, then paused before saying the thought aloud.",
        "dialogue": "'Ask me before you blame me,' {friend} said softly.",
        "action": "{name} asked, and {friend} explained that the thread came from mending the tool bag near the gears.",
        "twist": "The real culprit was a loose metal badge from the mayor's coat, which had scraped the panel during a hurried visit.",
        "resolution": "{name} and {friend} tightened the badge clasp, smoothed the panel, and opened the mechanism without another scratch.",
        "ending": "The brass whistle shone beside the repaired panel, and the friendship between them felt stronger than the mark.",
        "lesson": "caution protects both machines and trust",
    },
    {
        "title": "the hidden stair under the lock",
        "opening": "On a quiet evening, {name} and {friend} explored {setting} where the stones smelled of rain.",
        "mystery": "A draft came from beneath the lock chamber, though every door was shut.",
        "clue": "Dust had fallen in a straight line behind a stack of bucket weights, as if something moved there often.",
        "mistake": "{name} nearly moved the weights by hand, but the top one wobbled too much.",
        "dialogue": "'That stack is a warning sign all by itself,' {friend} said. 'Let's get a tool, not a bruise.'",
        "action": "{name} fetched a hook, and {friend} held the lantern while the weights were shifted one at a time.",
        "twist": "Under the stack was a narrow stair leading to an old reading nook where the lock keeper hid storybooks from the rain.",
        "resolution": "They left the books dry, set a notice on the stair, and replaced the weights so no one would stumble.",
        "ending": "The nook lamp glowed under the chamber floor, a secret made safe by careful hands.",
        "lesson": "mysteries should be opened with care, not force",
    },
    {
        "title": "the clockwork duck at the quay",
        "opening": "{name} spotted a tiny clockwork duck floating near {place} and called {friend} to the edge.",
        "mystery": "The duck circled three times, then tapped the dock with its beak like it wanted to speak.",
        "clue": "Its back hatch was full of sand, and one brass spring had been wound too tightly.",
        "mistake": "{name} reached to grab it from the water, but the current pulled the duck under the pier.",
        "dialogue": "'Wait for the net,' {friend} said. 'Even toys can turn tricky near water.'",
        "action": "{name} used the net while {friend} steadied the line, and the duck was lifted out without a splash.",
        "twist": "Inside the hatch was a message from a young inventor: the duck was a test, and the inventor had fallen asleep on the pier bench.",
        "resolution": "They woke the inventor, dried the duck, and heard how the spring was meant to pop open only after a full day in the sun.",
        "ending": "The duck bobbed again, brighter than before, while the inventor laughed with relief beside the quay.",
        "lesson": "caution keeps clever things from becoming accidents",
    },
    {
        "title": "the riddle at the boiler door",
        "opening": "At midnight, {name} and {friend} stood before the boiler door in {setting}, listening to a low hum.",
        "mystery": "A paper riddle had been taped to the handle, but the last line was smeared by steam.",
        "clue": "The clean words said, 'Do not open until the blue valve cools.'",
        "mistake": "{name} wanted to solve the riddle by opening the door anyway, just to see what was inside.",
        "dialogue": "'No mystery is worth a burn,' {friend} said. 'Let's read the warning first.'",
        "action": "{name} waited while {friend} found the blue valve and turned off the heat at the proper wheel.",
        "twist": "The boiler door held a kettle of soup for the night workers, and the riddle was their joke to keep impatient hands away.",
        "resolution": "They delivered the soup safely, and the workers thanked them for respecting the warning.",
        "ending": "Steam curled like a silver ribbon above the quiet boiler, and the joke felt kindly solved.",
        "lesson": "warnings can be part of the story, not obstacles to ignore",
    },
]


OPENINGS = [
    "At dusk, {name} and {friend} reached {setting} with {object_name} tucked in a pocket.",
    "When the moon rose, {name} and {friend} crossed {setting} to inspect {place}.",
    "At the old canal lock, {name} noticed {object_name} and called {friend} over at once.",
    "{name} and {friend} walked the towpath with {object_name} and a notebook full of questions.",
    "Near {place}, {name} found a scratch across {object_name} and felt the mystery begin.",
    "On a quiet evening, {name} and {friend} explored {setting} where the stones smelled of rain.",
    "{name} spotted a tiny clockwork duck floating near {place} and called {friend} to the edge.",
    "At midnight, {name} and {friend} stood before the boiler door in {setting}, listening to a low hum.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mystery world about mechanism, friendship, caution, and a twist.")
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--object-name")
    ap.add_argument("--place")
    ap.add_argument("--machine")
    ap.add_argument("--setting")
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
    name = args.name or rng.choice(["Lina", "Jae", "Mina", "Tobi", "Nora"])
    friend = args.friend or rng.choice(["Moss", "Pip", "Rue", "Bea", "Otto"])
    object_name = args.object_name or rng.choice(["the brass whistle", "a tiny key", "the blue lantern tag"])
    place = args.place or "the river gate"
    machine = args.machine or "bridge lift"
    setting = args.setting or "the old canal lock"
    if place not in {"the river gate", "the quay", "the lock chamber"}:
        raise StoryError("This world only supports the canal mystery setting.")
    if machine not in {"bridge lift", "lock wheel", "boiler door"}:
        raise StoryError("This world needs a small mechanism to solve.")
    return StoryParams(name=name, friend=friend, object_name=object_name, place=place, machine=machine, setting=setting)


def asp_facts() -> str:
    from storyworlds import asp

    return "\n".join(
        [
            asp.fact("mechanism", "bridge_lift"),
            asp.fact("feature", "friendship"),
            asp.fact("feature", "cautionary"),
            asp.fact("feature", "twist"),
            asp.fact("style", "mystery"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_story() -> bool:
    return True


def asp_verify() -> int:
    from storyworlds import asp

    model = asp.one_model(asp_program("#show safe_story/0."))
    asp_ok = bool(asp.atoms(model, "safe_story"))
    py_ok = python_reasonable_story()
    if asp_ok != py_ok:
        print(f"MISMATCH: asp={asp_ok} python={py_ok}")
        return 1
    sample = generate(StoryParams())
    if not sample.story or "?" in sample.story and "." not in sample.story:
        print("MISMATCH: generated story failed basic quality check")
        return 1
    print("OK: ASP and Python agree, and a generated story passed the sanity check.")
    return 0


def generate_story(world: World) -> None:
    p = world.params
    seed = p.seed or 0
    scenario = SCENARIOS[seed % len(SCENARIOS)]
    opening = OPENINGS[(seed // len(SCENARIOS)) % len(OPENINGS)]
    values = {
        "name": p.name,
        "friend": p.friend,
        "object_name": p.object_name,
        "place": p.place,
        "machine": p.machine,
        "setting": p.setting,
    }

    hero = world.add_character(Character(name=p.name, role="child"))
    friend = world.add_character(Character(name=p.friend, role="friend"))
    clue = world.add_object(ObjectThing(name=p.object_name, kind="clue"))

    hero.add_meme("curiosity", 1)
    friend.add_meme("loyalty", 1)

    world.say(opening.format(**values))
    world.say(f"The mystery of the evening was simple to say but hard to read: {scenario['mystery']}")
    world.say(f"{scenario['clue']}")
    world.say(f"{scenario['mistake']}")
    world.say(f"{scenario['dialogue']}")
    world.say(f"{scenario['action']}")
    world.say(f"{scenario['twist']}")
    world.say(f"{scenario['resolution']}")
    world.say(f"{scenario['ending']}")
    world.say(f"In the end, {scenario['lesson']}.")

    hero.add_meme("care", 1)
    hero.add_meter("steps", 7)
    friend.add_meter("help", 1)
    clue.add_meme("meaning", 1)

    world.facts = {
        "name": p.name,
        "friend": p.friend,
        "object_name": p.object_name,
        "place": p.place,
        "machine": p.machine,
        "setting": p.setting,
        "scenario": scenario["title"],
        "mystery": scenario["mystery"],
        "clue": scenario["clue"],
        "mistake": scenario["mistake"],
        "twist": scenario["twist"],
        "resolution": scenario["resolution"],
        "ending": scenario["ending"],
        "lesson": scenario["lesson"],
    }


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = world.params
    return [
        QAItem(
            question=f"What mystery did {p.name} and {p.friend} face?",
            answer=f"{f['mystery']} It felt strange because the mechanism was not behaving as expected at the setting.",
        ),
        QAItem(
            question="What clue helped them investigate safely?",
            answer=f"{f['clue']} That clue mattered because it pointed them toward the right place instead of the wrong guess.",
        ),
        QAItem(
            question="What cautionary mistake did the hero almost make?",
            answer=f"{f['mistake']} The story turns on the choice not to rush forward.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"{f['twist']} The twist changed suspicion into understanding.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{f['resolution']} The ending image was: {f['ending']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is friendship in this world?", answer="Friendship means helping, warning, and staying close when the mystery feels uncertain."),
        QAItem(question="What is cautionary?", answer="Cautionary means the story includes a warning that keeps someone safe or keeps a mistake from becoming worse."),
        QAItem(question="What is a twist?", answer="A twist is a surprise that changes what the characters thought was true."),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Tell a child-facing mystery story about {f['scenario']} with {f['machine']} at {f['setting']}.",
        f"Include a short spoken exchange where friendship changes a decision and caution prevents danger.",
        f"End with a concrete image proving the mystery was solved: {f['ending']}",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ch in world.characters.values():
        lines.append(f"  {ch.name} ({ch.role}) meters={ch.meters} memes={ch.memes}")
    for obj in world.objects.values():
        lines.append(f"  {obj.name} ({obj.kind}) meters={obj.meters} memes={obj.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(params=params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show safe_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        from storyworlds import asp

        model = asp.one_model(asp_program("#show safe_story/0."))
        print("safe_story" if asp.atoms(model, "safe_story") else "(no safe_story)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = resolve_params(args, random.Random(base_seed))
        params.seed = base_seed
        samples = [generate(params)]
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
