from openai import AsyncOpenAI
import openai, os, asyncio, argparse, json, sys
from tqdm.asyncio import tqdm
from mine_conceptnet import extract_assertions


def load_conceptnet(path):
    if not path:
        return {}
    out = {}
    with open(path) as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            out[rec.get("story_id")] = rec.get("assertions", [])
    return out


def format_conceptnet(assertions, limit=30):
    if not assertions:
        return ""
    groups = [
        ("Entities / kinds", {"IsA", "PartOf", "HasA", "MadeOf", "HasProperty", "DefinedAs"}),
        ("Affordances", {"UsedFor", "CapableOf", "AtLocation", "LocatedNear", "ReceivesAction", "HasPrerequisite", "HasSubevent"}),
        ("Causal / motivational rules", {"Causes", "CausesDesire", "Desires", "MotivatedByGoal", "ResolvesBy", "FeelsToward"}),
        ("Roles", {"CharacterRole"}),
    ]
    lines = ["## Mined ConceptNet facts for this story", ""]
    used = 0
    for title, rels in groups:
        rows = [a for a in assertions if a.get("relation") in rels]
        if not rows:
            continue
        lines.append(f"{title}:")
        for a in rows[:max(0, limit - used)]:
            lines.append(f"- {a.get('subject')} {a.get('relation')} {a.get('object')}  # {a.get('evidence')}")
            used += 1
            if used >= limit:
                break
        lines.append("")
        if used >= limit:
            break
    lines.append("Use these facts as semantic grounding for the story kernel, not as a separate output.")
    return "\n".join(lines)


async def extract_kernel(client, model, story, conceptnet_text=""):

    pairs = [
{"story" : """
Sophie liked to sit on a bench  
in a big, quiet park in Paris.  
She wore her headphones  
and looked at pictures on her phone.  
The park was peaceful,  
but she still felt a little lonely.

She felt something missing —  
a dream, a wind that never reached her.

Her dreams were of dragons and flight.  
But what she had was a bench and a phone.
One day, she saw something strange under the bench. It was a small book. The cover was soft like leather, and the pages were full of scribbles and drawings—like secret codes!
She almost put it back. But then… she opened it.
Inside were riddles—like puzzles—that talked about places in the park. 

> I stand so still, but wind,
> still finds me,
> shaking light where dreams unwind me.


Sophie was curious.
So, she stood up and followed the first clue.
Some clues were tricky! She got one wrong and ended up staring at a pigeon-filled courtyard for an hour. 
But soon, she started finding tiny treasures.

A shiny locket.
A dried flower in glass.  
A little broken compass.

They weren’t big treasures, but they felt special.  
Like someone had hidden them to be remembered.

She felt thirsty and frustrated when searching for the last clue.  

She sat on a bench and looked at her phone.  

But she took a few sips from her water bottle and continued.

No one saw her. 
No one helped. 

It got windy. She didn't mind. She was having fun.

The last clue talked about a big old tree:  

"Where the roots are always felt."  

She looked and looked.  
She was about to give up.  
The hollow was hard to find.  

Inside was a folded note,  
like the pages in the book.  

It simply said:  
> You are here.  
> The tree is always here.  
> And never the same.  
> Just like you.  

That was all.  

Sophie put the note back  
and hid the book inside.

She still likes to sit on a bench in a big, quiet park in Paris. 
She still wears her headphones and looks at her phone.

But now, when Wind plays with a kite and calls her name—
she smiles, and joins him.""",
"kernel": """
Sophie(Character, girl, Dreamy)
Journey(Sophie,
    state = Routine + Longing([Dragons, Flight]) + Loneliness / 10,
    catalyst = Surprise + Wind,
    process = Quest + Obstacles + Surrender / 5 + Persistence ,
    insight = Philosophical(Acceptance(Change)),
    transformation = Engaged(World) + Friendship(Sophie, Wind))
"""},

{ "story": """Once upon a time, there was a little cheerful boy named Leo. He loved playing outside and dancing in the rain. One day, Leo's mom bought him a clean white shirt. Leo loved his new shirt and wore it everywhere he went.
One rainy day, Leo and his mom went to the backyard. Leo wanted to play in the rain, but his mom said no. "You'll get your shirt soaking wet, and then I'll have to clean it," his mom said. Leo didn't want to listen and tried to run out into the rain, but his mom grabbed his hand and said, "You have to resist the urge to play in the rain today."
Leo pouted and crossed his arms. "But I want to play in the rain!" he said. His mom smiled and said, "How about we put on your rain boots first and play in the rain together?" Leo's face lit up and he hugged his mom. "Yay, let's do it!" he said as they went to get the rain boots.""",
"kernel": """
Leo(Character, boy, Cheerful + Playful)
Mom(Character, mother, Caring + Protective)
Shirt(Physical, clean + white, worn_by=Leo, region=torso)
RainBoots(Physical, Protective, guards=Wet, covers=[feet, legs])
Cautionary(Leo,
    desire = Play(Leo, object=rain) + Joy(Leo),
    risk = Predict(Mom, outcome=Wet(Shirt) + Dirty(Shirt) + Workload(Mom)),
    conflict = Warning(Mom, object=Leo) + Defiance(Leo) + Grab(Mom, object=Leo) + Pout(Leo),
    resolution = Compromise(Mom, object=Leo,
        plan=Use(RainBoots, action=Play(Leo, object=rain)) + Clean(Shirt) + Love(Leo, object=Mom)))"""
},


{ "story": """Once upon a time, there was a little boy named Tim. Tim loved to play with his red ball. He would kick it all day long. One day, Tim went outside to play. The air was icy, but he didn't care. He just wanted to play with his ball.\nTim kicked the ball high into the sky. He laughed as it went up and up. But then, the ball came down fast. Tim tried to catch it, but he missed. The ball hit him right in the face. Tim felt sad and his face hurt.\nTim went back inside his house. His mom saw his face and asked what happened. Tim told her about the ball. She hugged him and said, \"Be careful next time.\" Tim's face still hurt, and he didn't want to play with his ball anymore.""",
"kernel": """
Tim(Character, boy, Playful + Carefree)
Cautionary(Tim,
           event=Accident(Tim, process=Kick(ball) + Hit(face)),
           consequence=Pain(face) + Loss(Tim, Joy(ball) + Comfort(Mom, object=Tim)),
           lesson=Warning(Mom, object=Tim)
           )
)
"""}
]


    prompt = """
# Story Kernel Extraction Prompt

You are a narrative pattern extraction system. Your task is to analyze stories and extract their underlying "story kernels" - the composable narrative patterns that generate the surface text.

## Kernel Syntax Rules

### 1. Physical Objects vs Story Kernels
- **lowercase** = physical/concrete objects or actions (terminal nodes, no decomposition or internal Story)
  - Examples: `ball`, `face`, `bench`, `kick`, `hit`
  - These are physically grounded objects or actions - they don't contain other kernels
  
- **Proper Names** = Story kernels (memeplexes, composable narrative patterns)
  - Examples: `Joy`, `Journey`, `Pain`, `Insight`, `Dragons`, `Flight`, `Bad`
  - These can contain and compose other kernels

### 2. Composition Operators
- `\n` = sequence, temporal progression, use newline

- `+` = story mixture, co-occurrence
  - Example: `kick(ball) + hit(face)` means kick and hit
  - Example: `Routine + Longing` means both states coexist
  - Example: `small + Special` 
  - Example: `delicate and Kind`
  
- `/` = attention dilution, emphasis reduction
  - Example: `Hungry / 10`

- Parentheses `()` = story kernel application with arguments
  - Example: `Discovery(Sophie, object=book, location=under(bench))`

- Square brackets `[]` = lists of items
  - Example: `[locket, flower, compass]`

### 3. Structure Guidelines
- Always **Use single words** for kernels, NO spaces, NO underscores, NO hyphens, NO CamelCase
  - Good: `Discovery`, `Quest`, `Obstacle`, 'ball'
  - Good: `Cautionary + Twist`
  - Good: `Pain(face)`, `Not(Owner(dog))`
  - Good: `Guidance(guide=Mom, learner=Tim, lesson=Warning)`
  - ❌ WRONG - `FindTreasure` → Use: `Find + Treasure` 
  - ❌ WRONG - `PocketItToKeep(coin)` → Use: `Pocket(coin) + Keep` 
  - ❌ WRONG - `Findowner(coin)` → Use: `Find(Owner(coin))`
  - ❌ WRONG - `FindIfLost` → Use: `If(Lost, Find)`
  
- **Use ConceptNet-style argument names after the subject**. If a kernel has more
  than one semantic argument, keep the main actor/topic as the first positional
  argument (`subject`) and use `object=` for the related entity/concept. Use
  phase names like `process=`, `consequence=`, `lesson=`, `risk=`, or `plan=`
  only for story structure.
  - Good: `Warning(Mom, object=Tim)`, `Play(Leo, object=rain)`,
    `Compromise(Mom, object=Leo, plan=Use(RainBoots, action=Play(Leo, object=rain)))`
  - Avoid: `Warning(Mom, Tim)`, `Play(Leo, rain)`, `Compromise(Mom, Leo, plan)`
  
  
- **Preserve relational patterns** - if an element appears in multiple places (like `wind` in Longing and Transformation), keep it consistent
  
- **Nest kernels naturally** - composition should reflect narrative structure
  - `Accident(Tim, process=kick(ball) + hit(face), consequence=Pain + Loss)`

- **Chain kernels naturally** - keep linear narrative flow, when possible
    - `Journey(...)
       Insight(...)
       Transformation(...)`

- **Conditionals** - use `If(condition, story)` for a story conditional on another story

- **Separate character definitions** from story patterns
  - Start with: `Name(Character, traits)`
  - Then: story kernels

### 4. Abstraction Levels
Extract at multiple levels:

1. **Characters** - identify main characters, physical traits, assoacted memeplexes
2. **Meta-patterns** - high-level story structure (Cautionary, Twist, Journey)
3. **Compositional patterns** - sequences of actions (Quest, Accident)
4. **Atomic actions** - single discrete events (found, kicked, Learned)

## Example Extractions

### Example 1:

**Story:**
{story_1}

**Extracted Kernel:**
{kernel_1}

### Example 2:

**Story:**
{story_2}

**Extracted Kernel:**
{kernel_2}

### Example 3:

**Story:**
{story_3}

**Extracted Kernel:**
{kernel_3}

## Your Task

Extract the story kernel from the following story. Follow the syntax rules above. Structure your extraction to show:
1. Character definition(s) with traits
2. High-level meta-pattern (if applicable)
3. Nested compositional structure showing the narrative flow
4. Preserve any recurring elements that appear in multiple parts
5. Use single words for kernels, compose with + or new lines
6. Don't add extra commentary or headers


{conceptnet_facts}

**Story to analyze:**
{story}

**Extracted Kernel:**"""

    response = await client.chat.completions.create(
        model=model,

        messages=[
            {"role": "user", "content": prompt.format(
                story_1=pairs[0]["story"],
                kernel_1=pairs[0]["kernel"],
                story_2=pairs[1]["story"],
                kernel_2=pairs[1]["kernel"],
                story_3=pairs[2]["story"],
                kernel_3=pairs[2]["kernel"],
                conceptnet_facts=conceptnet_text,
                story=story
            )}
        ],
        temperature=0.0,
        max_tokens=4000,
    )
    choice = response.choices[0]
    content = choice.message.content
    if not content:
        print(f"[mine_kernels] empty kernel response; finish_reason={getattr(choice, 'finish_reason', None)}", file=sys.stderr)
        try:
            print(choice.model_dump_json(indent=2)[:2000], file=sys.stderr)
        except Exception:
            print(choice, file=sys.stderr)

    return content or ""



 
async def extract_test_case(story):
    localhost_base_url = os.environ.get("LOCALHOST_BASE_URL", "http://localhost:8001/v1")
    localhost_api_key = os.environ.get("LOCALHOST_API_KEY", "dummy-key")
    model = os.environ.get("MINE_MODEL", "gpt-oss-120b")
    client = AsyncOpenAI(api_key=localhost_api_key, base_url=localhost_base_url)
    record = {"story": story, "summary": "", "instruction": {"words": [], "features": []}}
    async with client:
        assertions = await extract_assertions(client, model, record, "test")
        conceptnet_text = format_conceptnet(assertions)
        kernel = await extract_kernel(client, model, story=story, conceptnet_text=conceptnet_text)
    return assertions, conceptnet_text, kernel


async def process_stories(stories, dataset, out_dir, conceptnet=None, limit=None):

    localhost_base_url = os.environ.get("LOCALHOST_BASE_URL", "http://localhost:8001/v1")
    localhost_api_key = os.environ.get("LOCALHOST_API_KEY", "dummy-key")
    
    client = AsyncOpenAI(api_key=localhost_api_key, base_url=localhost_base_url)
    model = "gpt-oss-120b"
    os.makedirs(out_dir, exist_ok=True)
    output_file = os.path.join(out_dir, f"{dataset}.kernels.jsonl")
    concurency = 32
    sem = asyncio.Semaphore(concurency)

    if limit is not None:
        stories = stories[:limit]

    async def limited_extract(idx, story):
        story_id = f"{dataset}:{idx}"
        conceptnet_text = format_conceptnet((conceptnet or {}).get(story_id, []))
        async with sem:
            kernel = await extract_kernel(client, model, story=story["story"],
                                          conceptnet_text=conceptnet_text)
            story["kernel"] = kernel
            if conceptnet_text:
                story["conceptnet_text"] = conceptnet_text
            return story

    async with client:
        tasks = [limited_extract(i, story) for i, story in enumerate(stories)]

        with open(output_file, 'w') as f:
            for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Extracting"):
                f.write(json.dumps(await task) + '\n')
                f.flush()  # Write immediately




if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", type=int, default=[3])
    ap.add_argument("--conceptnet", help="path to dataXX.assertions.jsonl from mine_conceptnet.py")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out-dir", help="write mined dataset kernels here; if unset, run only the test case")
    args = ap.parse_args()

    test = """John and Sarah were playing together in their backyard when they found a piece of metal. It was shiny and reflective and they couldn't wait to show their parents.
John asked Sarah, "What should we do with the metal?"
Sarah thought for a moment, then said, "Let's take it to Mommy and Daddy!" With that, they ran off excitedly, ready to surprise their parents.
They raced into the house, and shouted, "Mommy, Daddy! Look what we found!"
Their parents were very surprised and asked, "Where did you find this piece of metal?"
John and Sarah were so proud of their discovery, and couldn't wait to tell the story. They recounted that they found the metal outside in the backyard and it was so shiny and reflective.
Their parents smiled, and said, "Well, why don't you two take it around the neighbourhood and see if you can return it to its rightful owner. If nobody takes it, you two can keep it!".
John and Sarah were so cheerful and excited about the prospect of helping find the true owner of the metal, that they grabbed it and set off, ready to call on their neighbours.
"""

    if not args.out_dir:
        assertions, conceptnet_text, kernel = asyncio.run(extract_test_case(test))
        print(conceptnet_text)
        print()
        print(kernel)
        print(f"\n# assertions: {len(assertions)}")
        raise SystemExit(0)

    conceptnet = load_conceptnet(args.conceptnet)
    for i in args.datasets:
        dataset = f"data{i:02d}"
        with open(f"TinyStories_all_data/{dataset}.json", "r") as f:
            data = json.load(f)


        kernels = asyncio.run(process_stories(data, dataset, args.out_dir, conceptnet, args.limit))


