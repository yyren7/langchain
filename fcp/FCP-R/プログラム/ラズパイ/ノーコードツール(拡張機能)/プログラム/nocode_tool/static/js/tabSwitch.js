const tabs = document.querySelectorAll(".tabs .visual li a");
// const contents = document.querySelectorAll(".tabs .contents li");

for (let i = 0; i < tabs.length; i++){ 
  tabs[i].addEventListener("click", function(e){
    e.preventDefault();
  for (let j = 0; j < tabs.length; j++){ 
    tabs[j].classList.remove("active");
    // contents[j].classList.remove("active");
  }
    this.classList.add("active")
    tabs[i].classList.add("active")
    // contents[i].classList.add("active")
  });
}