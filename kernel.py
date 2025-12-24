from openai import AsyncOpenAI
import openai, os, asyncio
from tqdm.asyncio import tqdm


async def extract_kernel(client, model, story):

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

{ "story": """Once upon a time, there was a big whale. The whale loved to swim in the deep blue sea. The whale was very delicate and kind to all the little fish. 
One day, the whale wanted to test how fast he could swim. He swam and swam, faster and faster. All the fish cheered for the whale as he went by. The whale felt happy and strong.
But then, something unexpected happened. The whale found out he was not a whale, but a big, fast shark! The shark was still delicate and kind, and all the fish still liked him. They all swam and played together, happy in the deep blue sea.""",
"kernel": """
Whale(Character, Imaginary, Delicate + Kind)
Test(Speed) + Community(Support, cheered) + Happy
Identity(Whale,
         new=Shark,
         reaction=Acceptance + Community(Support, Liked))"""
},


{ "story": """Once upon a time, there was a little boy named Tim. Tim loved to play with his red ball. He would kick it all day long. One day, Tim went outside to play. The air was icy, but he didn't care. He just wanted to play with his ball.\nTim kicked the ball high into the sky. He laughed as it went up and up. But then, the ball came down fast. Tim tried to catch it, but he missed. The ball hit him right in the face. Tim felt sad and his face hurt.\nTim went back inside his house. His mom saw his face and asked what happened. Tim told her about the ball. She hugged him and said, \"Be careful next time.\" Tim's face still hurt, and he didn't want to play with his ball anymore.""",
"kernel": """
Tim(Character, boy, Playful + Carefree)
Cautionary(Tim,
           event=Accident(Tim, process=Kick(ball) + Hit(face)),
           consequence=Pain(face) + Loss(Tim, Joy(ball) + Comfort(Mom, Tim)),
           lesson=Warning(Mom, Tim)
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
  - Example: `Discovery(book, under(bench))`

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
                story=story
            )}
        ],
        temperature=0.0,
        max_tokens=1000,
    )
    #print(response['choices'][0]['message']['content'])

    return response.choices[0].message.content



 
async def process_stories(stories, dataset):

    localhost_base_url = os.environ.get("LOCALHOST_BASE_URL", "http://localhost:8001/v1")
    localhost_api_key = os.environ.get("LOCALHOST_API_KEY", "dummy-key")
    
    client = AsyncOpenAI(api_key=localhost_api_key, base_url=localhost_base_url)
    model = "gpt-oss-120b"
    output_file = f"{dataset}.kernels.jsonl"
    concurency = 32
    sem = asyncio.Semaphore(concurency)

    async def limited_extract(story):
        async with sem:
            kernel = await extract_kernel(client, model, story=story["story"])
            story["kernel"] = kernel
            return story

    async with client:
        tasks = [limited_extract(story) for story in stories]

        with open(output_file, 'w') as f:
            for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Extracting"):
                f.write(json.dumps(await task) + '\n')
                f.flush()  # Write immediately




if __name__ == "__main__":

    test = """John and Sarah were playing together in their backyard when they found a piece of metal. It was shiny and reflective and they couldn't wait to show their parents.
John asked Sarah, "What should we do with the metal?"
Sarah thought for a moment, then said, "Let's take it to Mommy and Daddy!" With that, they ran off excitedly, ready to surprise their parents.
They raced into the house, and shouted, "Mommy, Daddy! Look what we found!"
Their parents were very surprised and asked, "Where did you find this piece of metal?"
John and Sarah were so proud of their discovery, and couldn't wait to tell the story. They recounted that they found the metal outside in the backyard and it was so shiny and reflective.
Their parents smiled, and said, "Well, why don't you two take it around the neighbourhood and see if you can return it to its rightful owner. If nobody takes it, you two can keep it!".
John and Sarah were so cheerful and excited about the prospect of helping find the true owner of the metal, that they grabbed it and set off, ready to call on their neighbours.
"""

    #kernel = extract_kernel(test)
    #print(kernel)

    for i in range(3, 4):
        dataset = f"data{i:02d}"
        with open(f"TinyStories_all_data/{dataset}.json", "r") as f:
            import json
            data = json.load(f)


        kernels = asyncio.run(process_stories(data, dataset))


