import webbrowser

class Browser:
    def __init__(self):
        pass

    def search(self, query):
        """
        Opens a Google search for the given query.
        """
        if not query:
            return
        
        print(f"Browser: Searching for {query}")
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open_new_tab(url)
        return f"Searching for {query}"
        
    def smart_open(self, query):
        """
        Tries to open a direct URL for common sites, otherwise searches.
        """
        if not query: return
        
        q = query.lower().strip()
        common_sites = {
            "youtube": "https://www.youtube.com",
            "google": "https://www.google.com",
            "facebook": "https://www.facebook.com",
            "instagram": "https://www.instagram.com",
            "twitter": "https://www.twitter.com",
            "x": "https://www.twitter.com",
            "linkedin": "https://www.linkedin.com",
            "github": "https://www.github.com",
            "whatsapp": "https://web.whatsapp.com",
            "chatgpt": "https://chat.openai.com",
            "gmail": "https://mail.google.com",
            "amazon": "https://www.amazon.com",
            "netflix": "https://www.netflix.com",
            "spotify": "https://open.spotify.com",
            "reddit": "https://www.reddit.com"
        }
        
        if q in common_sites:
            url = common_sites[q]
            webbrowser.open_new_tab(url)
            return f"Opening {q}"
        else:
            # Fallback to search
            return self.search(query)

    def open_url(self, url):
        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open_new_tab(url)
        return f"Opening {url}"
