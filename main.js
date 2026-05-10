const EP_BASE_URL = "https://www.everyplate.com/gw";

const EP_MEAL_CATEGORIES = Object.freeze({

});

const EP_MEAL_CUISINES = Object.freeze({
    "american": 0,
    "asian": 1,
    "chinese": 2,
    "german": 3,
    "guacamole": 4,
    "indian": 5,
    "italian": 6,
    "japanese": 7,
    "korean": 8,
    "mediterranean": 9,
    "mexican": 10,
    "middle": 11,
    "pasta": 12,
    "spaghetti": 13,
    "thai": 14,
    "vietnamese": 15
});

class EPAuth {
    constructor() {
        this.loginResponse = null;
    }

    get authHeader() {
        if (!this.loginResponse) return null;

        let headers = new Headers();
        headers.append("authorization", `Bearer ${this.loginResponse.access_token}`);

        return headers;
    }

    get token() {
        if (!this.loginResponse) return null;
        return this.loginResponse.access_token;
    }

    get refreshToken() {
        if (!this.loginResponse) return null;
        return this.loginResponse.refresh_token;
    }

    get issued() {
        if (!this.loginResponse) return null;
        return this.loginResponse.issued_at;
    }

    isExpired() {
        if (!this.loginResponse) return null;
        return Date.now() > (this.loginResponse.issued_at + this.loginResponse.expires_in) * 1000;
    }

    isRefreshExpired() {
        if (!this.loginResponse) return null;
        return Date.now() > (this.loginResponse.issued_at + this.loginResponse.refresh_expires_in) * 1000;
    }

    isTokenValid() {
        return this.isExpired() !== null;
    }

    isRefreshValid() {
        return this.isRefreshExpired() !== null;
    }

    login(username, password) {
        return new Promise((resolve, reject) => {
            fetch(EP_BASE_URL + "/login?country=ER&locale=en-US", {
                method: "post",
                body: `{"username":"${username}", "password":"${password}"}`
            })
                .then(res => res.json())
                .then(json => {
                    this.loginResponse = json;
                    if ("error" in json)
                        reject(`Everyplate authorization failed: ${json.error} - ${json.error_description}`);
                    else
                        resolve("Everyplate authorization successful");
                })
                .catch(err => {
                    reject(`Everyplate authorization failed: ${err}`);
                });
        });
    }

    refresh() {
        return new Promise((resolve, reject) => {
            if (!this.isRefreshValid())
                return reject("Everyplate authorization refresh failed: Token Expired");

            fetch(EP_BASE_URL + "/refresh", {
                method: "post",
                body: `{"refresh_token": ${this.refreshToken}}`
            })
                .then(res => res.json())
                .then(json => {
                    this.loginResponse = json;
                    if ("error" in json)
                        reject(`Everyplate authorization refresh failed: ${json.error} - ${json.error_description}`);
                    else
                        resolve("Everyplate authorization refresh successful");
                })
                .catch(err => {
                    reject(`Everyplate authorization refresh failed: ${err}`);
                });
        });
    }
}

class EPSearch {
    constructor(auth, query) {
        this.auth = auth;
        this.searchURL = EP_BASE_URL + "/recipes/recipes/search?country=ER&locale=en-US" + query;
        this.resultsTotal = 0;
        this.resultsParsed = 0;
        this.pageSize = 30;
    }

    setPageSize(numResults) {
        const MIN_RESULTS = 2, MAX_RESULTS = 250;
        this.pageSize = Math.min(Math.max(numResults, MIN_RESULTS), MAX_RESULTS);
    }

    async getNextPage() {
        let pageQuery = this.searchURL + `&take=${this.pageSize}&skip=${this.resultsParsed}`;
        const res = await fetch(pageQuery, {
            headers:this.auth.authHeader
        });
        
        if (!res.ok)
            return console.error(`Everyplate search query failed: ${res.status} - ${res.statusText}`);

        const json = await res.json();
        this.resultsParsed += json.count;
        this.resultsTotal = json.total;

        return json.items;
    }

    async getAllResults() {
        let delayMs = ms => new Promise((res) => setTimeout(res, ms));
        
        this.resultsParsed = 0;
        let meals = await this.getNextPage();
        
        for(let i = this.resultsParsed; i < this.resultsTotal; i += this.pageSize) {
            let temp = await this.getNextPage();
            meals = meals.concat(temp);
            await delayMs(10);
        }

        return meals;
    }
}
