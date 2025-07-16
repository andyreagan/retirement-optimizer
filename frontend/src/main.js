import App from './App.svelte'

console.log('Main.js loaded')

const target = document.getElementById('app')
console.log('Target element:', target)

let app;

if (target) {
  app = new App({
    target: target
  })
  console.log('App created:', app)
} else {
  console.error('Could not find #app element')
}

export default app