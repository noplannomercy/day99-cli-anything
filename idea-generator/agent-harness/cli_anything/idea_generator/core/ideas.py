import random

IDEAS = {
    "writing": [
        "A character who can only tell the truth when singing",
        "Two enemies stuck in an elevator during a blackout",
        "A letter arrives 50 years late with a shocking secret",
        "The last person on Earth hears a knock at the door",
        "A child's imaginary friend turns out to be real",
        "A time traveler falls in love with someone from the past",
        "A detective solves crimes using dreams",
        "Strangers discover they share the same recurring nightmare",
        "A robot learns to feel emotions for the first time",
        "A writer's characters come to life and demand changes",
        "Two people meet at the same spot every year by coincidence",
        "A ghost tries to solve their own murder",
        "A world where everyone can read minds except one person",
        "A baker discovers their pastries grant wishes",
        "Siblings reunite after 20 years with different memories of their childhood",
        "A musician can hear colors and see sounds",
        "The moon disappears and only one person notices",
        "A librarian finds a book that writes itself",
        "A village where no one can lie after sunset",
        "Two strangers switch lives for a day and prefer the other's life",
    ],
    "drawing": [
        "A cityscape made entirely of food",
        "Portrait using only geometric shapes",
        "An animal wearing human clothes at work",
        "A tree that grows different objects instead of fruit",
        "Underwater city with fish as residents",
        "A dragon having afternoon tea",
        "House on clouds with rainbow bridges",
        "Robot gardening in a mechanical garden",
        "Cat astronaut exploring a cheese moon",
        "A library where books fly like birds",
        "Steampunk animal with mechanical parts",
        "A sunset scene using only warm colors",
        "Forest spirits having a midnight feast",
        "A shoe that's also a tiny house",
        "Weather emotions - what does happiness rain look like?",
        "A monster that's afraid of children",
        "Music visualized as a landscape",
        "A kitchen where ingredients cook themselves",
        "Time shown as a physical object",
        "A door between two completely different worlds",
    ],
    "business": [
        "Subscription service for busy parents needing quick meals",
        "Local marketplace connecting handmade artisans with buyers",
        "App that matches pet owners with trusted pet sitters",
        "Platform for seniors to teach skills to younger generations",
        "Service that converts old photos into digital art",
        "Eco-friendly packaging solution for small businesses",
        "Virtual event platform for niche hobby communities",
        "Personalized book recommendation service using AI",
        "Workspace sharing between night-shift and day-shift workers",
        "Sustainable fashion rental for special occasions",
        "Mental health app focused on workplace stress",
        "Grocery delivery service for specialty diet needs",
        "Tool that helps freelancers manage multiple clients",
        "Platform connecting local farmers with restaurants",
        "Service helping people downsize and declutter sustainably",
        "App for neighbors to share tools and equipment",
        "Personalized vitamin subscription based on health data",
        "Remote team building activity marketplace",
        "Service that plans surprise experiences for loved ones",
        "Platform for micro-volunteering opportunities",
    ],
    "coding": [
        "Build a markdown editor with live preview",
        "Create a CLI tool for organizing files by type",
        "Pomodoro timer with statistics tracking",
        "Personal finance tracker with visual charts",
        "Weather app that suggests outfit recommendations",
        "Recipe finder based on available ingredients",
        "Habit tracker with streak visualization",
        "Bookmark manager with automatic categorization",
        "Simple drawing app with shape recognition",
        "Music playlist generator based on mood",
        "Note-taking app with tag-based organization",
        "Code snippet manager with syntax highlighting",
        "Personal dashboard aggregating daily info",
        "Browser extension that blocks distracting sites",
        "Password generator with strength indicator",
        "Simple kanban board for personal tasks",
        "Typing speed test with progress tracking",
        "Color palette generator from images",
        "URL shortener with click analytics",
        "Daily journal app with mood tracking",
    ],
}

CATEGORIES = list(IDEAS.keys())

# In-memory last idea per category (no immediate repeats within a session)
_last_idea: dict = {}


def get_random_idea(category: str) -> str | None:
    if category not in IDEAS:
        return None
    pool = IDEAS[category]
    if len(pool) == 1:
        return pool[0]
    idea = _last_idea.get(category)
    candidates = [i for i in pool if i != idea]
    chosen = random.choice(candidates)
    _last_idea[category] = chosen
    return chosen
