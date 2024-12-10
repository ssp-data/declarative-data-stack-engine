# Declarative Data Stack Engine

This is the implementation from the article of [The Rise of the Declarative Data Stack](https://www.rilldata.com/blog/the-rise-of-the-declarative-data-stack) and the code for [Part 3]().


## SDF

### Authenticate

```sh
❯ sdf auth login aws --profile default
    Confirm Saved AWS auth configuration
   Finished auth in 0.330 secs

❯ sdf auth login aws --profile default --default-region us-east-2
    Confirm Saved AWS auth configuration
   Finished auth in 0.324 secs

❯ sdf run -e remote --show all
```

