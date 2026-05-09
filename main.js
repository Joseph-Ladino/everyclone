class EveryAuth {
    constructor(username, password) {
        this.#username = username;
        this.#password = password;
        this.authURL = "https://www.everyplate.com/gw/login?country=ER&locale=en-US";
        this.loginResponse = null;
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

    login() {
        return new Promise((resolve, reject) => {
            fetch(this.authURL, {
                method: "post",
                body: `{"password":"${this.#password}","username":"${this.#username}"}`
            })
            .then(res => res.json())
            .then(json => {
                this.loginResponse = json;
                resolve("Everyplate Authorization successful");
            })
            .catch(err => {
                reject(`Everyplate Authorization failed: ${err}`);
            });
        });
    }

    refresh() {
        // TODO: figure out refresh token api
    }
}