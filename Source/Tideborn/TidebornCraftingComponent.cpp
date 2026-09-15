#include "TidebornCraftingComponent.h"
#include "TidebornInventoryComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Components/InputComponent.h"
#include "Engine/Engine.h"
#include "TimerManager.h"
#include "Engine/World.h"

UTidebornCraftingComponent::UTidebornCraftingComponent()
{
	PrimaryComponentTick.bCanEverTick = false;

	{
		FTidebornRecipe R;
		R.RecipeId = FName(TEXT("Stick"));
		R.Costs.Add({FName(TEXT("Wood")), 2});
		R.Output = {FName(TEXT("Stick")), 1};
		Recipes.Add(R);
	}
	{
		FTidebornRecipe R;
		R.RecipeId = FName(TEXT("Foundation"));
		R.Costs.Add({FName(TEXT("Wood")), 5});
		R.Output = {FName(TEXT("Foundation")), 1};
		Recipes.Add(R);
	}
	{
		FTidebornRecipe R;
		R.RecipeId = FName(TEXT("CampfireKit"));
		R.Costs.Add({FName(TEXT("Stick")), 3});
		R.Costs.Add({FName(TEXT("Stone")), 2});
		R.Output = {FName(TEXT("CampfireKit")), 1};
		Recipes.Add(R);
	}
}

void UTidebornCraftingComponent::BeginPlay()
{
	Super::BeginPlay();
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateUObject(this, &UTidebornCraftingComponent::BindHotkeys));
	}
}

UTidebornInventoryComponent* UTidebornCraftingComponent::GetInventory() const
{
	return GetOwner() ? GetOwner()->FindComponentByClass<UTidebornInventoryComponent>() : nullptr;
}

void UTidebornCraftingComponent::BindHotkeys()
{
	APawn* Pawn = Cast<APawn>(GetOwner());
	APlayerController* PC = Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
	if (!PC && GetWorld())
	{
		PC = GetWorld()->GetFirstPlayerController();
	}
	if (!PC)
	{
		if (UWorld* World = GetWorld())
		{
			FTimerHandle Handle;
			World->GetTimerManager().SetTimer(Handle, this, &UTidebornCraftingComponent::BindHotkeys, 0.25f, false);
		}
		return;
	}

	UInputComponent* IC = PC->InputComponent;
	if (!IC)
	{
		IC = Pawn ? Pawn->InputComponent : nullptr;
	}
	if (!IC)
	{
		if (UWorld* World = GetWorld())
		{
			FTimerHandle Handle;
			World->GetTimerManager().SetTimer(Handle, this, &UTidebornCraftingComponent::BindHotkeys, 0.25f, false);
		}
		return;
	}

	IC->BindKey(EKeys::C, IE_Pressed, this, &UTidebornCraftingComponent::OnCraftKey);
	IC->BindKey(EKeys::I, IE_Pressed, this, &UTidebornCraftingComponent::OnInventoryKey);
	UE_LOG(LogTemp, Log, TEXT("TidebornCraft: bound C/I"));
}

void UTidebornCraftingComponent::OnCraftKey()
{
	TryCraftFirstAffordable();
}

void UTidebornCraftingComponent::OnInventoryKey()
{
	if (UTidebornInventoryComponent* Inv = GetInventory())
	{
		Inv->PrintInventory();
	}
	PrintRecipes();
}

bool UTidebornCraftingComponent::TryCraft(FName RecipeId)
{
	UTidebornInventoryComponent* Inv = GetInventory();
	if (!Inv)
	{
		return false;
	}

	const FTidebornRecipe* Found = Recipes.FindByPredicate([&](const FTidebornRecipe& R) { return R.RecipeId == RecipeId; });
	if (!Found)
	{
		return false;
	}

	if (!Inv->HasItems(Found->Costs))
	{
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(-1, 2.f, FColor::Orange, FString::Printf(TEXT("Tideborn Craft need more for %s"), *RecipeId.ToString()));
		}
		return false;
	}

	for (const FTidebornItemStack& Cost : Found->Costs)
	{
		Inv->RemoveItem(Cost.ItemId, Cost.Count);
	}
	Inv->AddItem(Found->Output.ItemId, Found->Output.Count);

	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(-1, 2.5f, FColor::Yellow, FString::Printf(TEXT("Tideborn Crafted %s x%d"), *Found->Output.ItemId.ToString(), Found->Output.Count));
	}
	return true;
}

void UTidebornCraftingComponent::TryCraftFirstAffordable()
{
	UTidebornInventoryComponent* Inv = GetInventory();
	if (!Inv)
	{
		return;
	}
	for (const FTidebornRecipe& R : Recipes)
	{
		if (Inv->HasItems(R.Costs))
		{
			TryCraft(R.RecipeId);
			return;
		}
	}
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(-1, 2.f, FColor::Orange, TEXT("Tideborn: nothing affordable to craft (I for recipes)"));
	}
}

void UTidebornCraftingComponent::PrintRecipes() const
{
	for (const FTidebornRecipe& R : Recipes)
	{
		FString Line = FString::Printf(TEXT("Recipe %s -> %s x%d | costs:"), *R.RecipeId.ToString(), *R.Output.ItemId.ToString(), R.Output.Count);
		for (const FTidebornItemStack& C : R.Costs)
		{
			Line += FString::Printf(TEXT(" %s x%d"), *C.ItemId.ToString(), C.Count);
		}
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(-1, 5.f, FColor::White, Line);
		}
	}
}
