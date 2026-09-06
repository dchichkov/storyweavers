#!/usr/bin/env python3
"""
Story world: bulls at a marina, a lullabye, a transformation, a friendship, and a gentle mystery.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wears: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    marina: str = "harbor marina"
    hero: str = "Nina"
    companion: str = "Toby"
    bull: str = "Brindle"
    seed: Optional[int] = None


SCENARIOS = (
    {
        "name": "the silent buoy",
        "mystery": "the red channel buoy had stopped chiming whenever the evening ferry passed",
        "clue": "a strand of blue sailcloth was caught beneath its sound shield",
        "wrong": "They first blamed the fog for swallowing the bell's sound",
        "cause": "a loose festival banner was muffling the buoy",
        "response": "the harbor crew retrieved the cloth from their workboat and secured every banner ashore",
        "line": '"The same blue thread is on the welcome arch," the companion noticed',
        "change": "The quiet bull lifted his head at the restored, gentle chime instead of pacing",
        "ending": "the buoy gave one silver note while the bull's reflection rested between two mooring lights",
        "lesson": "good friends test a clue before they accuse the weather",
    },
    {
        "name": "the wandering lanterns",
        "mystery": "three solar lanterns appeared in a new place along the quay each morning",
        "clue": "tiny wheel marks curved from the lantern rack toward a sloping drain",
        "wrong": "They wondered whether a night visitor was rearranging them as a secret message",
        "cause": "the unlocked rack rolled a little whenever the tide lifted a floating ramp",
        "response": "a dockworker chocked the rack's wheels and painted its safe parking outline",
        "line": '"The trail bends downhill, not toward a hiding place," the hero said',
        "change": "The nervous bull stopped flinching at wandering pools of light once the lanterns stayed put",
        "ending": "three steady circles of gold shone beside the bull's straw bed",
        "lesson": "curiosity becomes useful when friends measure what moved and why",
    },
    {
        "name": "the missing lullabye",
        "mystery": "the last line of the marina's old lullabye had vanished from the song board",
        "clue": "faint reversed letters showed through the damp paper backing",
        "wrong": "They suspected someone had torn away the ending because it sounded silly",
        "cause": "the final lyric had been pasted backward during a hurried rain repair",
        "response": "the archivist softened the paste, turned the strip over, and mounted it beneath clear cover",
        "line": '"It is not gone; it is facing the wall," the companion whispered',
        "change": "When everyone sang the complete lullabye, the bull settled and the shy companion joined the chorus",
        "ending": "the recovered words glimmered under glass as the final note crossed the water",
        "lesson": "friends look twice before deciding that something has been lost",
    },
    {
        "name": "the knocking hull",
        "mystery": "a hollow knock answered every lullabye from an empty training boat",
        "clue": "the knocks matched the small waves rather than the rhythm of the song",
        "wrong": "For a moment they imagined that someone was trapped below deck",
        "cause": "a padded fender had slipped behind the hull and tapped at each rise of the water",
        "response": "the boat owner pulled the fender into view and retied it at the correct height",
        "line": '"Sing once, then pause and watch the wave," the hero proposed',
        "change": "The companion changed from frightened guessing to patient observation, and the bull mirrored that calm",
        "ending": "the boat rocked without knocking, and a round fender bobbed neatly beside its cleat",
        "lesson": "bravery can mean waiting long enough to notice a pattern",
    },
    {
        "name": "the salt-white hoofprints",
        "mystery": "white hoof-shaped marks crossed a locked dock beyond the bulls' secure pen",
        "clue": "each mark had straight brush edges and smelled faintly of chalk, not mud",
        "wrong": "They feared a bull had somehow left the supervised enclosure",
        "cause": "an art volunteer had tested footprint stencils for the marina's farm-benefit trail",
        "response": "the volunteer labeled the test area and the handler counted every bull safely inside the pen",
        "line": '"Real hooves would not leave square corners," the companion reasoned',
        "change": "Relief replaced suspicion, and the children thanked the handler for checking first",
        "ending": "chalk hoofprints led visitors to the benefit tent while the real bulls chewed hay behind two latched gates",
        "lesson": "a startling shape is evidence to examine, not proof by itself",
    },
    {
        "name": "the blue ribbon",
        "mystery": "a blue ribbon kept disappearing from the livestock shelter's award hook",
        "clue": "salt crystals sparkled on the ribbon whenever it returned",
        "wrong": "The friends briefly suspected a jealous exhibitor",
        "cause": "a gust from the vent lifted the ribbon into a rain barrel beside the outside wall",
        "response": "the caretaker moved the hook, covered the barrel, and clipped up the dried ribbon",
        "line": '"The ribbon visited the same salty puddle every time," the hero said',
        "change": "The bull's young caretaker admitted the loose hook instead of hiding the mistake, strengthening the friendship",
        "ending": "the ribbon stayed above Brindle's nameplate, blue as the strip of evening sea",
        "lesson": "telling the truth gives friends something real to repair",
    },
    {
        "name": "the humming rope",
        "mystery": "a mooring rope hummed the first notes of a lullabye only after sunset",
        "clue": "the sound stopped whenever a deckhand loosened the line by one careful notch",
        "wrong": "They wondered if a hidden music box was tied beneath the dock",
        "cause": "the cooling rope tightened across a hollow metal fairlead and vibrated in the breeze",
        "response": "the dockmaster adjusted the line safely and added a soft protective sleeve",
        "line": '"The rope is acting like one enormous string," the companion said',
        "change": "What had sounded eerie became a lesson in wind and tension, and the bull no longer turned toward it",
        "ending": "the sleeved rope lay quiet while the friends hummed its old tune from behind the viewing rail",
        "lesson": "mysteries grow smaller when friends change one condition at a time",
    },
    {
        "name": "the green water pail",
        "mystery": "one bull's sealed water pail looked green each afternoon but clear each morning",
        "clue": "a green safety flag reflected in the surface only when the sun reached the west window",
        "wrong": "The children worried that algae had suddenly filled the fresh water",
        "cause": "sunlight bounced the flag's color through the shelter window",
        "response": "the handler tested the water, replaced it as scheduled, and moved the flag away from the window",
        "line": '"Let us ask the handler to test it; color alone cannot tell us if it is safe," the hero said',
        "change": "The companion learned to report an animal-care concern without reaching into the enclosure",
        "ending": "clear water held a small square of sunset while the green flag fluttered across the yard",
        "lesson": "kindness means reporting a concern and letting trained caretakers check it",
    },
    {
        "name": "the double whistle",
        "mystery": "the harbor master's single safety whistle always seemed to answer itself",
        "clue": "the second note came only beside the curved roof of the livestock shelter",
        "wrong": "They searched for another person signaling from the fog",
        "cause": "the shelter roof reflected the whistle as a crisp echo",
        "response": "the team marked an alternate signal station where echoes could not confuse workers",
        "line": '"One call, one reflection," the companion counted after a careful test',
        "change": "The confusing signal became a safer marina procedure",
        "ending": "one clean whistle crossed the dusk, followed only by the soft rustle of hay",
        "lesson": "friends improve a system when a discovery could keep others safe",
    },
    {
        "name": "the untied weather vane",
        "mystery": "the brass bull weather vane pointed toward the sea even when every flag blew inland",
        "clue": "a crescent scratch circled the base where the arrow should have turned",
        "wrong": "They joked that the metal bull wanted to visit the boats",
        "cause": "a grain of windblown sand had jammed the vane's bearing",
        "response": "the maintenance worker lowered, cleaned, and reinstalled the vane from a closed work zone",
        "line": '"The flags agree with one another, so the vane needs checking," the hero concluded',
        "change": "The companion's joke became a sound hypothesis, then a respectful request for expert help",
        "ending": "the brass bull turned inland with the flags as the real bull slept below",
        "lesson": "playful ideas can lead to careful tests when friends listen",
    },
    {
        "name": "the unopened gate alarm",
        "mystery": "the secure livestock gate chimed at midnight although its seal remained unbroken",
        "clue": "the alarm log showed each chime exactly when the ice maker began its cleaning cycle",
        "wrong": "The caretaker feared someone had tried to open the bull enclosure",
        "cause": "a shared loose cable carried vibration from the nearby utility wall to the gate sensor",
        "response": "an electrician separated the cable mounts and the handler tested the alarm without opening the occupied pen",
        "line": '"The seal says the gate stayed shut; the clock may tell us what else started," the companion said',
        "change": "Careful records transformed a frightening alarm into a repairable equipment fault",
        "ending": "the green gate light held steady while cubes clicked harmlessly into the marina cafe's bin",
        "lesson": "records help friends separate what seemed to happen from what actually happened",
    },
    {
        "name": "the moonlit bell",
        "mystery": "a tiny bell rang near the bull shelter whenever moonlight reached the eastern dock",
        "clue": "the bell fell silent when a passing cloud covered a solar garden ornament",
        "wrong": "They thought the lullabye-loving bull might be nudging the bell for a song",
        "cause": "the ornament's light sensor was wired backward and started its chime in brightness",
        "response": "the exhibit maker switched it off, corrected the sensor, and mounted it outside the animal area",
        "line": '"The bull is behind both gates, but the moon keeps touching that silver panel," the hero observed',
        "change": "The friends stopped giving the bull human motives and learned to read the physical clues",
        "ending": "moonlight silvered the silent ornament while the bull breathed slowly beneath a clean blanket",
        "lesson": "friendship with an animal includes respecting its space and understanding its behavior",
    },
)

OPENINGS = (
    "The first clue arrived just before the marina lamps came on.",
    "A puzzle was waiting where the working docks met the temporary livestock shelter.",
    "The evening began with a sound that did not belong where it seemed to be.",
    "At low tide, two friends noticed that the marina's ordinary routine had changed.",
    "Fog curled between the masts when the harbor master asked two careful observers for help.",
    "After the last tour group left, one small detail refused to make sense.",
    "The bulls from the coastal farm were resting safely when a marina mystery interrupted the quiet.",
    "No one was in danger, but something at the marina plainly needed explaining.",
)

TRANSITIONS = (
    "Instead of deciding too soon, they wrote down what changed and what stayed the same.",
    "They compared the timing, the weather, and the marks without crossing the safety rail.",
    "The pair asked the responsible worker for permission, then observed from the public path.",
    "They traded theories, rejected the ones that did not fit, and kept the strongest clue.",
    "A short lullabye helped everyone listen between the ordinary harbor noises.",
    "They drew a simple clue map and invited the caretaker to check it with them.",
    "Their first idea failed, so they changed one condition and watched again.",
    "Friendship made disagreement useful: one watched the water while the other watched the clock.",
)

QA_STYLES = (
    ("What puzzled the friends about {scenario}?", "What evidence changed their minds?", "What was the hidden cause?", "Who handled the safe repair?", "How did someone change?", "What idea did the friends carry home?"),
    ("Which marina mystery involved {scenario}?", "Which detail pointed toward the answer?", "What finally explained the puzzle?", "How did the group respond without approaching the bull?", "What transformation followed the discovery?", "What did the experience teach the friends?"),
    ("Why did {scenario} need investigating?", "What clue did {hero} and {companion} use?", "What had really happened?", "How was the marina made safe again?", "What changed after the mystery was solved?", "Which lesson fit the evidence?"),
    ("What unusual event began the case of {scenario}?", "What observation helped solve it?", "What caused the unusual event?", "What safe action resolved the problem?", "How did the solution transform the situation?", "What lesson completed the story?"),
)

LULLABYES = (
    "Rest by the rail where the calm tides flow; night holds the harbor steady and slow.",
    "Hush now, harbor, soften your light; boats are at anchor and all gates are right.",
    "Moon over mast and star over bay; breathe with the water till worry drifts away.",
    "Low sings the wind and quiet lies the foam; every tired traveler has a sheltered home.",
    "Rock, little ripple, under the moon; morning will find us, but not too soon.",
    "Lanterns are glowing, the workday is done; rest until silver gives way to the sun.",
)


@dataclass
class World:
    marina: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        import copy
        return World(self.marina, copy.deepcopy(self.entities), [[]], dict(self.facts), set(self.fired))


def _narrate_name(entity: Entity) -> str:
    return entity.label or entity.id


def tell(params: StoryParams) -> World:
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = SCENARIOS[rng.randrange(len(SCENARIOS))]
    opening = OPENINGS[rng.randrange(len(OPENINGS))]
    transition = TRANSITIONS[rng.randrange(len(TRANSITIONS))]
    lullabye = LULLABYES[rng.randrange(len(LULLABYES))]
    investigation_order = rng.randrange(4)

    world = World(params.marina)
    hero = world.add(Entity(id=params.hero, kind="character", type="girl", label=params.hero, traits=["curious", "kind"]))
    companion = world.add(Entity(id=params.companion, kind="character", type="boy", label=params.companion, traits=["nervous", "loyal"]))
    bull = world.add(Entity(id=params.bull, kind="animal", type="bull", label=params.bull))
    clue = world.add(Entity(id="clue", kind="thing", type="evidence", label=scenario["clue"], phrase=scenario["clue"]))
    role_names = {
        "the hero": hero.id,
        "The hero": hero.id,
        "the companion": companion.id,
        "The companion": companion.id,
        "Brindle": bull.id,
    }

    def personalize(text: str) -> str:
        for role, name in role_names.items():
            text = text.replace(role, name)
        return text

    change = personalize(scenario["change"])
    ending = personalize(scenario["ending"])

    hero.memes.update(curiosity=1, friendship=1)
    companion.memes.update(bravery=1, friendship=1)
    bull.meters.update(secure=1, calm=0, transformed=0)
    world.facts = {
        "hero": hero.id,
        "companion": companion.id,
        "bull": bull.id,
        "scenario": scenario["name"],
        "mystery": scenario["mystery"],
        "clue": scenario["clue"],
        "wrong": scenario["wrong"],
        "cause": scenario["cause"],
        "response": scenario["response"],
        "change": change,
        "ending": ending,
        "lesson": scenario["lesson"],
        "lullabye": lullabye,
        "qa_style": rng.randrange(len(QA_STYLES)),
    }

    world.say(opening)
    world.say(
        f"At the {world.marina}, {hero.id} and {companion.id} were visiting bulls temporarily sheltered from a coastal storm. "
        f"Trained handlers cared for {bull.label} behind two latched livestock gates; the children stayed on the public side of the viewing rail."
    )
    world.say(f"Their mystery was this: {scenario['mystery']}.")
    world.para()

    observations = [
        f"{scenario['wrong']}.",
        f"Then {hero.id} found the useful clue: {clue.phrase}.",
        f"{personalize(scenario['line'])}.",
        transition,
    ]
    if investigation_order == 1:
        observations[1], observations[2] = observations[2], observations[1]
    elif investigation_order == 2:
        observations = [observations[3], observations[0], observations[2], observations[1]]
    elif investigation_order == 3:
        observations = [observations[0], observations[3], observations[1], observations[2]]
    for sentence in observations:
        world.say(sentence)

    world.say(
        f"While the authorized workers checked the clue, {hero.id} sang the marina lullabye from behind the rail: "
        f'"{lullabye}"'
    )
    bull.meters["calm"] = 1
    bull.memes["peace"] = 1
    world.para()

    world.say(f"The evidence revealed the cause: {scenario['cause']}.")
    world.say(f"To solve it safely, {scenario['response']}.")
    world.say(f"The transformation was clear: {change[0].lower() + change[1:]}.")
    bull.meters["transformed"] = 1
    hero.memes["mystery_solved"] = 1
    companion.memes["mystery_solved"] = 1

    if rng.randrange(2):
        world.say(
            f'"We did not need to be fearless," {companion.id} told {hero.id}. '
            f'"We needed to be careful together." {hero.id} answered that this was what friendship looked like.'
        )
    else:
        world.say(
            f"The friendship changed too: {hero.id} began asking for {companion.id}'s observations, "
            f"and {companion.id} began offering them without waiting to feel completely brave."
        )
    world.para()
    world.say(f"They carried home the lesson that {scenario['lesson']}.")
    world.say(f"That night, {ending}.")
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a child-friendly mystery set at the {world.marina} about {facts['scenario']}; include safely sheltered bulls and a lullabye.",
        f"Tell how two friends use this clue, {facts['clue']}, to discover that {facts['cause']}.",
        f"Write a gentle transformation story ending with this image: {facts['ending']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    questions = [
        text.format(
            scenario=facts["scenario"],
            hero=facts["hero"],
            companion=facts["companion"],
        )
        for text in QA_STYLES[facts["qa_style"]]
    ]
    return [
        QAItem(
            question=questions[0],
            answer=f"The friends needed to explain why {facts['mystery']}.",
        ),
        QAItem(
            question=questions[1],
            answer=f"They noticed that {facts['clue']}. That evidence fit the real cause better than their first guess.",
        ),
        QAItem(
            question=questions[2],
            answer=f"They discovered that {facts['cause']}.",
        ),
        QAItem(
            question=questions[3],
            answer=f"The children stayed behind the livestock barrier while {facts['response']}.",
        ),
        QAItem(
            question=questions[4],
            answer=f"{facts['change']}. The friends also changed by trusting careful evidence and each other.",
        ),
        QAItem(
            question=questions[5],
            answer=f"They learned that {facts['lesson']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a marina?",
            answer="A marina is a place where boats are kept, tied up, and cared for near the water.",
        ),
        QAItem(
            question="What is a lullabye?",
            answer="A lullabye is a soft song that helps someone relax or go to sleep.",
        ),
        QAItem(
            question="What is a bull?",
            answer="A bull is an adult male bovine. People should observe bulls from a safe distance and leave their care to trained handlers.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- character(H).
bull(B) :- animal(B), bull_type(B).
drowsy_bull(B) :- bull(B), drowsy(B).
calmed(B) :- drowsy_bull(B), lullabye(S).
friendship(H,B) :- character(H), bull(B), calmed(B), kind(H).
transformed(B) :- bull(B), calmed(B).
mystery(H) :- character(H), clue(H), hidden_problem(H).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("character", "nina"),
        asp.fact("character", "toby"),
        asp.fact("animal", "brindle"),
        asp.fact("bull_type", "brindle"),
        asp.fact("clue", "nina"),
        asp.fact("hidden_problem", "nina"),
        asp.fact("lullabye", "song"),
        asp.fact("kind", "nina"),
        asp.fact("kind", "toby"),
        asp.fact("drowsy", "brindle"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show calmed/1.\n#show friendship/2.\n#show transformed/1.\n"))
    shown = set((s.name, len(s.arguments)) for s in model)
    need = {("calmed", 1), ("friendship", 2), ("transformed", 1)}
    if shown >= need:
        print("OK: ASP rules produce the expected story facts.")
        return 0
    print("MISMATCH: ASP rules did not produce expected facts.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A marina mystery about bulls, a lullabye, friendship, and transformation.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--marina", default="harbor marina")
    ap.add_argument("--hero", default=None)
    ap.add_argument("--companion", default=None)
    ap.add_argument("--bull", default=None)
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(["Nina", "Mara", "Ivy", "Ada"])
    companion = args.companion or rng.choice(["Toby", "Eli", "Finn", "Owen"])
    bull = args.bull or rng.choice(["Brindle", "Patch", "Bramble", "Moss"])
    return StoryParams(marina=args.marina, hero=hero, companion=companion, bull=bull)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show calmed/1.\n#show friendship/2.\n#show transformed/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show calmed/1.\n#show friendship/2.\n#show transformed/1.\n"))
        print("\n".join(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams())]
    else:
        seen = set()
        i = 0
        while len(samples) < max(1, args.n) and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
