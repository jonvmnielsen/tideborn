#include "TidebornMenuWidgets.h"
#include "TidebornUIComponent.h"
#include "TidebornCraftingComponent.h"
#include "TidebornInventoryComponent.h"
#include "Components/VerticalBox.h"
#include "Components/TextBlock.h"
#include "Components/Button.h"
#include "Components/Border.h"
#include "Blueprint/WidgetTree.h"

void UTidebornRecipeButtonWidget::Setup(UTidebornUIComponent* InUI, FName InRecipeId, const FString& Label)
{
	OwnerUI = InUI;
	RecipeId = InRecipeId;
	PendingLabel = Label;
	if (LabelText)
	{
		LabelText->SetText(FText::FromString(PendingLabel));
	}
}

void UTidebornRecipeButtonWidget::NativeConstruct()
{
	Super::NativeConstruct();
	if (!WidgetTree)
	{
		return;
	}
	Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("Btn"));
	WidgetTree->RootWidget = Button;
	LabelText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("Lbl"));
	LabelText->SetText(FText::FromString(PendingLabel.IsEmpty() ? TEXT("Recipe") : PendingLabel));
	LabelText->SetAutoWrapText(true);
	Button->AddChild(LabelText);
	Button->OnClicked.AddDynamic(this, &UTidebornRecipeButtonWidget::HandleClick);
}

void UTidebornRecipeButtonWidget::HandleClick()
{
	if (OwnerUI)
	{
		OwnerUI->CraftSelectedOrRecipe(RecipeId);
	}
}

void UTidebornInventoryMenuWidget::SetOwnerUI(UTidebornUIComponent* InUI)
{
	OwnerUI = InUI;
}

void UTidebornInventoryMenuWidget::NativeConstruct()
{
	Super::NativeConstruct();

	UBorder* Root = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("RootBorder"));
	WidgetTree->RootWidget = Root;
	Root->SetBrushColor(FLinearColor(0.02f, 0.03f, 0.05f, 0.94f));
	Root->SetPadding(FMargin(20.f));

	UVerticalBox* RootBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("RootBox"));
	Root->SetContent(RootBox);

	TitleText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("Title"));
	TitleText->SetText(FText::FromString(TEXT("Inventory & Crafting")));
	RootBox->AddChildToVerticalBox(TitleText);

	BodyText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("Body"));
	BodyText->SetAutoWrapText(true);
	RootBox->AddChildToVerticalBox(BodyText);

	UTextBlock* Hint = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("Hint"));
	Hint->SetText(FText::FromString(TEXT("Click a recipe to craft. I or Close exits this menu.")));
	Hint->SetAutoWrapText(true);
	RootBox->AddChildToVerticalBox(Hint);

	RecipeBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("Recipes"));
	RootBox->AddChildToVerticalBox(RecipeBox);

	CloseButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("CloseBtn"));
	UTextBlock* CloseLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("CloseLabel"));
	CloseLabel->SetText(FText::FromString(TEXT("Close menu")));
	CloseButton->AddChild(CloseLabel);
	CloseButton->OnClicked.AddDynamic(this, &UTidebornInventoryMenuWidget::OnCloseClicked);
	RootBox->AddChildToVerticalBox(CloseButton);
}

void UTidebornInventoryMenuWidget::OnCloseClicked()
{
	if (OwnerUI)
	{
		OwnerUI->CloseAllMenus();
	}
}

void UTidebornInventoryMenuWidget::Refresh()
{
	if (!OwnerUI)
	{
		return;
	}

	UTidebornInventoryComponent* Inv = OwnerUI->GetInventory();
	FString InvLine = TEXT("Items:\n");
	bool bAny = false;
	if (Inv)
	{
		for (const FTidebornItemStack& InvSlot : Inv->Slots)
		{
			if (!InvSlot.IsEmpty())
			{
				bAny = true;
				InvLine += FString::Printf(TEXT("• %s x%d\n"), *InvSlot.ItemId.ToString(), InvSlot.Count);
			}
		}
	}
	if (!bAny)
	{
		InvLine += TEXT("(empty)\n");
	}
	if (BodyText)
	{
		BodyText->SetText(FText::FromString(InvLine));
	}

	if (!RecipeBox)
	{
		return;
	}
	RecipeBox->ClearChildren();

	if (UTidebornCraftingComponent* Craft = OwnerUI->GetCrafting())
	{
		for (int32 i = 0; i < Craft->Recipes.Num(); ++i)
		{
			const FTidebornRecipe& R = Craft->Recipes[i];
			FString Costs;
			for (const FTidebornItemStack& C : R.Costs)
			{
				const int32 Have = Inv ? Inv->CountItem(C.ItemId) : 0;
				Costs += FString::Printf(TEXT(" %s %d/%d"), *C.ItemId.ToString(), Have, C.Count);
			}
			const FString Label = FString::Printf(TEXT("%s  → %s x%d |%s"),
				*R.RecipeId.ToString(), *R.Output.ItemId.ToString(), R.Output.Count, *Costs);

			UTidebornRecipeButtonWidget* Row = CreateWidget<UTidebornRecipeButtonWidget>(this, UTidebornRecipeButtonWidget::StaticClass());
			if (Row)
			{
				Row->Setup(OwnerUI, R.RecipeId, Label);
				RecipeBox->AddChildToVerticalBox(Row);
			}
		}
	}
}

void UTidebornBuildMenuWidget::SetOwnerUI(UTidebornUIComponent* InUI)
{
	OwnerUI = InUI;
}

void UTidebornBuildMenuWidget::NativeConstruct()
{
	Super::NativeConstruct();

	UBorder* Root = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("BuildRoot"));
	WidgetTree->RootWidget = Root;
	Root->SetBrushColor(FLinearColor(0.06f, 0.04f, 0.02f, 0.95f));
	Root->SetPadding(FMargin(20.f));

	UVerticalBox* Box = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("BuildBox"));
	Root->SetContent(Box);

	TitleText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("BuildTitle"));
	TitleText->SetText(FText::FromString(TEXT("Build Menu")));
	Box->AddChildToVerticalBox(TitleText);

	HelpText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("BuildHelp"));
	HelpText->SetAutoWrapText(true);
	HelpText->SetText(FText::FromString(TEXT(
		"Click a piece to start placing.\n"
		"Then: WASD move, mouse look, Left-click place, Right-click cancel.\n"
		"Foundation costs 1 Foundation item (craft from 5 Wood in Inventory).")));
	Box->AddChildToVerticalBox(HelpText);

	FoundationButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("FoundationBtn"));
	FoundationLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("FoundationLbl"));
	FoundationLabel->SetText(FText::FromString(TEXT("Foundation")));
	FoundationButton->AddChild(FoundationLabel);
	FoundationButton->OnClicked.AddDynamic(this, &UTidebornBuildMenuWidget::OnFoundationClicked);
	Box->AddChildToVerticalBox(FoundationButton);

	CloseButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("BuildClose"));
	UTextBlock* CLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("BuildCloseLbl"));
	CLabel->SetText(FText::FromString(TEXT("Close menu")));
	CloseButton->AddChild(CLabel);
	CloseButton->OnClicked.AddDynamic(this, &UTidebornBuildMenuWidget::OnCloseClicked);
	Box->AddChildToVerticalBox(CloseButton);
}

void UTidebornBuildMenuWidget::Refresh()
{
	if (!OwnerUI || !FoundationLabel)
	{
		return;
	}
	UTidebornInventoryComponent* Inv = OwnerUI->GetInventory();
	const int32 Have = Inv ? Inv->CountItem(FName(TEXT("Foundation"))) : 0;
	FoundationLabel->SetText(FText::FromString(
		FString::Printf(TEXT("Foundation — owned: %d  (click to place)"), Have)));
}

void UTidebornBuildMenuWidget::OnCloseClicked()
{
	if (OwnerUI)
	{
		OwnerUI->CloseAllMenus();
	}
}

void UTidebornBuildMenuWidget::OnFoundationClicked()
{
	if (OwnerUI)
	{
		OwnerUI->StartPlacingFoundation();
	}
}


