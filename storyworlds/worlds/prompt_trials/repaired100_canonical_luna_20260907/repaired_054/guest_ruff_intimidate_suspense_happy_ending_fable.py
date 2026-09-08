#!/usr/bin/env python3
"""A fable-like StoryWorld about a guest, a rough ruff, and brave kindness."""

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
    setting: str = "the moonlit meadow"
    guest_name: str = "Luna"
    host_name: str = "Milo"
    ruff_name: str = "Ruff"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    welcome: str
    trouble: str
    intimidation: str
    clue: str
    plan: str
    jobs: tuple[str, str]
    turn: str
    result: str
    lesson: str
    ending: str


SETTINGS = {
    "the moonlit meadow": True,
    "the village garden": True,
    "the old orchard": True,
    "the lantern-lit barn": True,
}
NAMES = ["Luna", "Milo", "Nora", "Pip", "Tessa", "Bram", "Ivy", "Finn"]
RUFF_NAMES = ["Ruff", "Brindle", "Growler", "Scruff"]

SCENARIOS = [
    Scenario(
        "gate-shadow",
        "A kindly guest arrived carrying a basket of honey cakes.",
        "A rough ruff sprang from behind the gate and blocked the narrow path.",
        "Its shaggy ruff rose high, and its deep bark made the lanterns tremble.",
        "the dog wore a small bell that jingled whenever it was frightened",
        "speak softly, leave a cake on the ground, and give the dog a wide path",
        ("held the lantern low so the dog could see friendly hands", "placed the cake by the gate and stepped back"),
        "The ruff sniffed the cake, lowered its fur, and moved aside.",
        "gentleness can turn a warning into a welcome",
        "the guest entered beneath the moon while the little bell rang like a happy star",
    ),
    Scenario(
        "bridge-bark",
        "A cheerful guest came to share warm bread beside the stream.",
        "A rough ruff stood on the footbridge and barked whenever anyone came near.",
        "The bridge shook under the loud barking, and the guest could not see the far bank.",
        "a strip of blue cloth was tied to the rail where the dog had once been helped",
        "show the cloth, call the dog by name, and cross only when the bridge was still",
        ("held the bread where the scent could reach the dog", "kept one hand on the rail and watched the water"),
        "The dog remembered the helping hand and let the guest cross.",
        "understanding an old fear is wiser than answering it with anger",
        "bread was shared on the far bank, and the ruff curled beside the bridge like a guard at peace",
    ),
    Scenario(
        "thorny-welcome",
        "A small guest came to visit a fox who lived beside a thorn hedge.",
        "A rough ruff snarled from the hedge, making the guest's bright ribbon catch on a thorn.",
        "The guest froze while the thorny branches whispered in the wind.",
        "the ruff's paw was caught in the same hedge beneath a fallen branch",
        "help the frightened dog first, then free the guest's ribbon together",
        ("pushed the branch aside with a sturdy stick", "untangled the paw and loosened the ribbon"),
        "The ruff stopped snarling and nudged the ribbon free.",
        "a creature in trouble may look fierce because it needs help",
        "the ribbon fluttered between guest and ruff as both walked safely from the hedge",
    ),
    Scenario(
        "echo-cave",
        "A curious guest brought a bright shell to a cave at the hill's foot.",
        "A rough ruff's bark echoed from inside, sounding like many angry animals.",
        "The echoes grew louder, and the guest nearly dropped the shell.",
        "one echo stopped whenever the shell was tapped softly",
        "tap a gentle rhythm, wait for an answer, and enter only with the ruff's consent",
        ("tapped three quiet notes against the shell", "stood near the entrance and listened for the reply"),
        "The ruff answered with one soft bark and came into the light.",
        "patience can reveal that a frightening sound has a gentle source",
        "the shell shone beside the ruff's nose while the cave held a peaceful echo",
    ),
    Scenario(
        "stormy-yard",
        "A guest arrived with a red umbrella as dark clouds gathered.",
        "A rough ruff charged around the yard, barking at every flash of lightning.",
        "A sudden thunderclap made the ruff rush toward the guest.",
        "the dog kept glancing at the empty kennel behind the rain barrel",
        "guide the ruff toward its dry kennel and hold the umbrella over both of them",
        ("opened the umbrella wide to soften the flashing sky", "set a trail of biscuits toward the kennel"),
        "The ruff followed the trail and rested safely before the next thunderclap.",
        "fear may make a good heart act roughly, so offer shelter before blame",
        "when the storm passed, the guest and ruff shared biscuits beneath a clear silver sky",
    ),
    Scenario(
        "bell-tower",
        "A guest climbed the hill to bring a lost key to the bell keeper.",
        "A rough ruff guarded the path and growled whenever the key shone.",
        "The key flashed like a tiny tooth, and the guest dared not step forward.",
        "the bell keeper's ribbon was tied around the dog's collar",
        "cover the key, ring the bell softly, and let the dog hear the keeper's call",
        ("wrapped the key in a blue cloth", "rang one slow note and waited beside the steps"),
        "The ruff heard its keeper, wagged its tail, and escorted the guest upward.",
        "a calm signal can do what force cannot",
        "the returned key opened the bell tower, and the ruff received the first warm pat",
    ),
    Scenario(
        "garden-fountain",
        "A guest came to admire a fountain where birds gathered at dusk.",
        "A rough ruff stood beside the fountain and would not let anyone approach.",
        "Its bark scattered the birds, leaving the garden strangely still.",
        "the water bowl was empty, though the fountain basin was full",
        "fill the bowl, step away, and let the thirsty dog choose peace",
        ("carried water in a small wooden cup", "placed the cup beside the bowl and waited quietly"),
        "The ruff drank, then bowed its head while the birds returned.",
        "care often opens a door that commands keep shut",
        "the fountain sparkled again as guest, ruff, and birds shared the quiet garden",
    ),
    Scenario(
        "harvest-cart",
        "A guest brought apples to a village harvest feast.",
        "A rough ruff blocked the cart and frightened every pony nearby.",
        "One pony tugged the reins, and the cart began to roll toward a ditch.",
        "the dog's paw was pinned beneath one wheel",
        "steady the pony, free the paw, and let the ruff see that help had come",
        ("held the reins with both hands and spoke slowly", "lifted the wheel with a wooden lever"),
        "The ruff was freed and stood still while the cart was guided away from the ditch.",
        "even a frightening guard may be guarding a hidden hurt",
        "the apples reached the feast, where the grateful ruff slept beneath the cart",
    ),
    Scenario(
        "winter-door",
        "A guest knocked at a cottage door with a scarf for the baker.",
        "A rough ruff guarded the porch and growled at the unfamiliar visitor.",
        "Snow muffled every sound except the dog’s warning growl.",
        "the scarf smelled of the baker's warm kitchen",
        "place the scarf near the door, wait in the snow, and let the familiar scent speak",
        ("folded the scarf on the clean doorstep", "kept a respectful distance beneath the eaves"),
        "The ruff sniffed the scarf and wagged when the baker opened the door.",
        "trust grows when strangers are given time and space",
        "the baker welcomed the guest inside, and the ruff shared the warm mat by the fire",
    ),
    Scenario(
        "firefly-path",
        "A guest followed fireflies toward a hidden picnic clearing.",
        "A rough ruff appeared in the path and barked whenever the fireflies flew ahead.",
        "The guest could not tell whether the dog was warning or chasing them.",
        "the fireflies gathered around a broken lantern behind the ruff",
        "repair the lantern first and invite the dog to watch the steady light",
        ("held the lantern pieces together", "tied them with a strip of picnic cloth"),
        "The lantern glowed, and the ruff stopped chasing the fireflies.",
        "a shared task can change strangers into companions",
        "the fireflies danced above the picnic while the ruff rested beside the new light",
    ),
    Scenario(
        "river-stone",
        "A guest came to return a smooth blue stone to the riverbank.",
        "A rough ruff barked from the stepping stones and made the crossing seem impossible.",
        "The guest's foot slipped, and cold water swirled around the stone.",
        "the ruff was watching a pup stranded on the opposite bank",
        "save the pup with a branch, then return the stone when the ruff is calm",
        ("held the branch across the narrowest gap", "called softly until the pup reached the bank"),
        "The ruff guided the pup away and let the guest place the stone by the river.",
        "shared care makes room for courage",
        "the blue stone gleamed in the shallows while the grateful ruff watched from the grass",
    ),
    Scenario(
        "lantern-feast",
        "A guest carried a lantern to a feast beneath the apple trees.",
        "A rough ruff rushed from the shadows and seemed ready to intimidate everyone.",
        "The feast grew silent, and even the crickets stopped their song.",
        "the ruff's shadow was large, but its body trembled beneath the table",
        "lower the lantern, speak kindly, and offer a place beside the warm fire",
        ("shielded the flame so it would not startle the dog", "made a soft nest from a folded feast cloth"),
        "The ruff crept into the nest and accepted a gentle greeting.",
        "a brave welcome can uncover a frightened heart",
        "music returned to the feast, and the guest saved the sweetest apple for the ruff",
    ),
]


OPENINGS = [
    "At twilight, {guest} came to {setting}, where every leaf seemed to listen.",
    "One golden evening, {guest} arrived at {setting} with a hopeful heart.",
    "The moon had just climbed above {setting} when {guest} appeared at the gate.",
    "In {setting}, a stranger's footsteps began a small and suspenseful adventure.",
    "A quiet path led {guest} toward {setting}, carrying a gift and a question.",
    "The animals of {setting} were settling down when {guest} came to visit.",
]

REACTIONS = [
    "'Do not run,' whispered {guest}. 'A frightened heart may bark loudly.'",
    "{guest} held still. 'I will listen before I decide what you mean.'",
    "'Something is wrong,' said {guest}. 'Let us look carefully.'",
    "The guest's knees trembled, but kindness was stronger than the first fright.",
    "'I am not here to take anything,' {guest} called softly.",
    "For a moment, the path seemed darker than the night sky.",
]

MORALS = [
    "The wisest creature asks what fear is protecting before answering fear with fear.",
    "A gentle deed can be a lantern for two frightened hearts.",
    "Bravery is not loudness; it is choosing care while danger still feels near.",
    "A stranger becomes less strange when both sides are given time to listen.",
    "The heart that pauses to help may find a friend waiting beneath the growl.",
]

RUFF_ACTIONS = [
    "The ruff lifted one paw and watched closely.",
    "The ruff's ears twitched beneath its rough ruff.",
    "The dog gave a warning bark, then waited.",
    "The ruff paced once, twice, and looked toward the clue.",
]

def generate_world(p: StoryParams) -> World:
    if p.guest_name == p.host_name:
        raise StoryError("The guest and host must have different names.")
    if p.guest_name == p.ruff_name:
        raise StoryError("The guest and ruff must have different names.")

    world = World(p.setting)
    guest = world.add(Entity("guest", "character", p.guest_name))
    host = world.add(Entity("host", "character", p.host_name))
    ruff = world.add(Entity("ruff", "animal", p.ruff_name))

    seed = abs(p.seed or 0)
    scene = SCENARIOS[seed % len(SCENARIOS)]
    opening = OPENINGS[(seed // 13) % len(OPENINGS)]
    reaction = REACTIONS[(seed // 29) % len(REACTIONS)]
    ruff_action = RUFF_ACTIONS[(seed // 47) % len(RUFF_ACTIONS)]
    moral = MORALS[(seed // 71) % len(MORALS)]

    world.say(opening.format(guest=guest.label, setting=p.setting))
    world.say(f"{host.label} had invited {guest.label}, but {ruff.label}, the household's rough ruff, stood near the way.")
    world.say(scene.welcome)
    world.para()
    world.say(scene.trouble)
    world.say(scene.intimidation)
    world.say(reaction.format(guest=guest.label))
    world.say(f"{ruff.label} {ruff_action.lower()}")
    world.say(f"Then {guest.label} noticed that {scene.clue}.")
    world.para()
    world.say(f"'{scene.plan.capitalize()},' said {host.label}.")
    world.say(f"{guest.label} replied, 'I will help, but we must leave room for {ruff.label} to choose.'")
    world.say(f"{guest.label} {scene.jobs[0]}, while {host.label} {scene.jobs[1]}.")
    world.say(f"The suspense held the meadow quiet. Then {scene.turn}")
    world.say(scene.result)
    world.para()
    world.say(f"{host.label} smiled. 'You were a brave guest, {guest.label}.'")
    world.say(f"{guest.label} answered, 'And {ruff.label} was not a monster. {ruff.label} needed kindness.'")
    world.say(f"The fable's lesson was clear: {moral}")
    world.say(f"In the happy ending, {scene.ending}")

    guest.meters.update(safety=1.0, courage=1.0)
    host.meters.update(safety=1.0, trust=1.0)
    ruff.meters.update(fear=0.0, calm=1.0)
    guest.memes.update(kindness=1.0, bravery=1.0)
    host.memes.update welcome=1.0, trust=1.0)
    ruff.memes.update(trust=1.0, friendship=1.0)

    world.facts.update(
        guest=guest.label,
        host=host.label,
        ruff=ruff.label,
        scenario=scene.key,
        trouble=scene.trouble,
        intimidation=scene.intimidation,
        clue=scene.clue,
        plan=scene.plan,
        guest_job=scene.jobs[0],
        host_job=scene.jobs[1],
        turn=scene.turn,
        result=scene.result,
        moral=moral,
        ending=scene.ending,
        happy=True,
        safe=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Why did {f['guest']} feel suspense?",
            answer=f"{f['guest']} felt suspense because {f['trouble']} {f['intimidation']}",
        ),
        QAItem(
            question="What clue changed the guest's understanding?",
            answer=f"The clue was that {f['clue']}. It showed that the rough ruff might be frightened or in need of help.",
        ),
        QAItem(
            question="How did the guest and host solve the problem?",
            answer=f"They planned to {f['plan']}. {f['guest']} {f['guest_job']}, while {f['host']} {f['host_job']}.",
        ),
        QAItem(
            question="What happened when their plan worked?",
            answer=f"{f['turn']} {f['result']}",
        ),
        QAItem(
            question="How did the fable end?",
            answer=f"The story ended happily because the guest and ruff became safe and friendly. {f['ending']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a guest?",
            answer="A guest is someone invited to visit another person or place.",
        ),
        QAItem(
            question="What is a ruff?",
            answer="A ruff is a thick or rough collar of fur around an animal's neck.",
        ),
        QAItem(
            question="What does intimidate mean?",
            answer="To intimidate means to make someone feel afraid or less brave.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the worried excitement people feel while waiting to learn what will happen.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending resolves the danger and leaves the characters safe, wiser, or kindly connected.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a fable about guest {f['guest']} meeting the rough ruff {f['ruff']}.",
        f"Tell a suspenseful but child-friendly story in {world.setting} where kindness changes the danger.",
        f"Create a happy ending in which the guest learns that {f['clue']}.",
    ]


ASP_RULES = r"""
safe_guest(G,R) :- guest(G), ruff(R), clue(R), kind_plan(G).
happy_ending(G,R) :- safe_guest(G,R), calmed(R), welcomed(G).
fable_solution(G,R) :- happy_ending(G,R).
#show safe_guest/2.
#show happy_ending/2.
#show fable_solution/2.
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("guest", "luna"),
        asp.fact("guest", "nora"),
        asp.fact("ruff", "ruff"),
        asp.fact("ruff", "brindle"),
        asp.fact("clue", "ruff"),
        asp.fact("clue", "brindle"),
        asp.fact("kind_plan", "luna"),
        asp.fact("kind_plan", "nora"),
        asp.fact("calmed", "ruff"),
        asp.fact("calmed", "brindle"),
        asp.fact("welcomed", "luna"),
        asp.fact("welcomed", "nora"),
    ]
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(asp_program("#show fable_solution/2."))
    found = asp.atoms(symbols, "fable_solution")
    if found:
        print("OK: ASP found a safe guest and calmed ruff.")
        return 0
    print("MISMATCH: ASP found no happy fable ending.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--guest-name")
    parser.add_argument("--host-name")
    parser.add_argument("--ruff-name")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    guest = args.guest_name or rng.choice(NAMES)
    host_choices = [name for name in NAMES if name != guest]
    host = args.host_name or rng.choice(host_choices)
    ruff = args.ruff_name or rng.choice(RUFF_NAMES)
    if guest == host:
        raise StoryError("The guest and host must have different names.")
    if guest == ruff:
        raise StoryError("The guest and ruff must have different names.")
    return StoryParams(
        setting=args.setting or rng.choice(sorted(SETTINGS)),
        guest_name=guest,
        host_name=host,
        ruff_name=ruff,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("the moonlit meadow", "Luna", "Milo", "Ruff", 7),
    StoryParams("the old orchard", "Nora", "Pip", "Brindle", 31),
    StoryParams("the lantern-lit barn", "Tessa", "Bram", "Scruff", 83),
]


def emit(sample: StorySample, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        facts = sample.world.facts
        print(
            "\n--- world model state ---\n"
            f"scenario={facts['scenario']} safe={facts['safe']} happy={facts['happy']}"
        )
    if qa:
        for index, item in enumerate(sample.story_qa, 1):
            print(f"Q{index}: {item.question}\nA{index}: {item.answer}")
        for index, item in enumerate(sample.world_qa, 1):
            print(f"W{index}: {item.question}\nA{index}: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_guest/2. #show happy_ending/2. #show fable_solution/2."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    base = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base + index)
            params = resolve_params(args, rng)
            params.seed = base + index
            samples.append(generate(params))

    if args.asp:
        import asp

        symbols = asp.one_model(asp_program("#show fable_solution/2."))
        if not asp.atoms(symbols, "fable_solution"):
            raise StoryError("ASP reasonableness check found no happy ending.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], ensure_ascii=False, indent=2))
        return

    for index, sample in enumerate(samples):
        emit(sample, args.trace, args.qa, f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
