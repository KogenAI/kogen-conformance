defmodule GreetTest do
  use ExUnit.Case

  @tag intent: "greet/A1"
  test "greets World" do
    assert Hello.greet() == "Hello, World!"
  end
end
