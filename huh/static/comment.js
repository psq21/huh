document.addEventListener("DOMContentLoaded", (event) => {
  const chats = document.querySelectorAll(".chat");
  const ids = Array.from(document.querySelectorAll(".chat > .comment_id")).map((el) => el.textContent.trim());
  const editBtns = document.querySelectorAll(".edit-btn");
  const chatBubbles = document.querySelectorAll(".chat-bubble");

  editBtns.forEach((editBtn, index) => {
    const chatBubble = chatBubbles[index];
    const chat = chats[index];
    const id = ids[index];
    let originalContent = chatBubble.textContent;

    const editEvent = () => {
      originalContent = chatBubble.textContent;
      chatBubble.innerHTML = `
          <div class="flex flex-col gap-2 items-center">
              <textarea class="textarea textarea-bordered text-black" placeholder="Comment something...">${originalContent.trim()}</textarea>
              <div class="flex gap-2">
                  <button class="btn btn-info save-btn h-2">Save</button>
                  <button class="btn btn-error delete-btn h-2">Delete</button>
              </div>
          </div>
          `;

      // handle on save
      const saveBtn = chatBubble.querySelector(".save-btn");
      saveBtn.addEventListener("click", () => {
        const newContent = chatBubble.querySelector("textarea").value;
        chatBubble.textContent = newContent;
        originalContent = newContent;
        editBtn.innerHTML = `
              <img src="../../static/pencil.svg"
                     class="h-4 w-4"
                     alt="Edit">
              `;
        editBtn.addEventListener("click", editEvent);
        const fd = new FormData();
        fd.append("content", newContent);

        fetch(`/comment/update/${id}`, {
          method: "PUT",
          body: fd,
        }).then((res) => {
          if (res.ok) {
            console.log("Comment updated successfully");
          } else {
            console.error("Failed to update comment");
          }
        });
      });

      // handle on delete
      const deleteBtn = chatBubble.querySelector(".delete-btn");
      deleteBtn.addEventListener("click", () => {
        chat.remove();
        fetch(`/comment/delete/${id}`, {
          method: "DELETE",
        }).then((res) => {
          if (res.ok) {
            console.log("Comment deleted successfully");
          } else {
            console.error("Failed to delete comment");
          }
        });
      });

      // handle cancel -- revert to original content
      // the original edit button will change to a cancel button
      editBtn.innerHTML = `
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
          `;
      editBtn.removeEventListener("click", editEvent);
      editBtn.addEventListener("click", () => {
        chatBubble.textContent = originalContent;
        editBtn.innerHTML = `
              <img src="../../static/pencil.svg"
                     class="h-4 w-4"
                     alt="Edit">
              `;
        editBtn.addEventListener("click", editEvent);
        
      });
    };

    editBtn.addEventListener("click", editEvent);
  });
});
